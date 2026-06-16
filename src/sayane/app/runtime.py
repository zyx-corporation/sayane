"""Resident runtime builder for local app command wiring.

This module keeps resident command assembly separate from CLI, Bridge routes,
and concrete storage adapters. Runtime storage selection is centralized here so
entrypoints do not construct repository backends directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, cast

from sayane.app.capabilities import CapabilityToken, create_local_capability_token
from sayane.app.service import ResidentAppService
from sayane.bridge.config import BridgeConfig
from sayane.storage.repositories import RepositoryBundle


class ResidentRepositoryBackend(StrEnum):
    """Supported resident repository backend selection modes."""

    LEGACY_PROCESS_LOCAL = "legacy_process_local"
    INJECTED_REPOSITORY_BUNDLE = "injected_repository_bundle"
    SQLITE_TEST_LOCAL_VAULT = "sqlite_test_local_vault"
    FUTURE_PRO_BACKEND = "future_pro_backend"


@dataclass(frozen=True)
class ResidentRepositorySelection:
    """Resolved repository selection for a resident runtime."""

    backend: ResidentRepositoryBackend
    repositories: RepositoryBundle | None = None
    storage_boundary: str = "none"
    vault_runtime: Any | None = None
    notes: tuple[str, ...] = ()

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive repository selection diagnostics."""
        return {
            "backend": self.backend.value,
            "has_repositories": self.repositories is not None,
            "storage_boundary": self.storage_boundary,
            "notes": list(self.notes),
        }


@dataclass(frozen=True)
class ResidentRuntime:
    """Assembled resident runtime boundary for local commands."""

    service: ResidentAppService
    bridge_config: BridgeConfig
    repository_selection: ResidentRepositorySelection
    capabilities: dict[str, CapabilityToken] = field(default_factory=dict)

    def describe(self) -> dict[str, Any]:
        """Return non-sensitive runtime diagnostics."""
        payload = self.service.describe()
        payload["bridge_host"] = self.bridge_config.host
        payload["bridge_port"] = self.bridge_config.port
        payload["capabilities"] = sorted(self.capabilities)
        payload["repository_backend"] = self.repository_selection.backend.value
        payload["storage_boundary"] = self.repository_selection.storage_boundary
        payload["repository_selection"] = self.repository_selection.public_metadata()
        return payload


def _coerce_repository_backend(
    value: ResidentRepositoryBackend | str,
) -> ResidentRepositoryBackend:
    if isinstance(value, ResidentRepositoryBackend):
        return value
    try:
        return ResidentRepositoryBackend(value)
    except ValueError as exc:
        supported = ", ".join(backend.value for backend in ResidentRepositoryBackend)
        message = (
            f"Unsupported resident repository backend: {value!r}. "
            f"Supported: {supported}"
        )
        raise ValueError(message) from exc


def select_resident_repositories(
    *,
    profile_id: str = "default",
    repository_backend: ResidentRepositoryBackend | str | None = None,
    repositories: RepositoryBundle | None = None,
    vault_path: Path | None = None,
    allow_test_vault: bool = False,
) -> ResidentRepositorySelection:
    """Resolve resident repository selection behind one app/runtime boundary.

    CLI, UI, Bridge, and MCP callers should use this runtime seam instead of
    importing concrete SQLite or future backend builders directly.
    """
    if repository_backend is None:
        backend = (
            ResidentRepositoryBackend.INJECTED_REPOSITORY_BUNDLE
            if repositories is not None
            else ResidentRepositoryBackend.LEGACY_PROCESS_LOCAL
        )
    else:
        backend = _coerce_repository_backend(repository_backend)

    if backend is ResidentRepositoryBackend.LEGACY_PROCESS_LOCAL:
        if repositories is not None:
            raise ValueError("repositories require injected_repository_bundle backend")
        return ResidentRepositorySelection(
            backend=backend,
            storage_boundary="none",
            notes=(
                "legacy process-local fallback only; not a production durable "
                "resident state store",
            ),
        )

    if backend is ResidentRepositoryBackend.INJECTED_REPOSITORY_BUNDLE:
        if repositories is None:
            raise ValueError("injected_repository_bundle requires repositories")
        return ResidentRepositorySelection(
            backend=backend,
            repositories=repositories,
            storage_boundary="repository_bundle",
            notes=(
                "caller supplied RepositoryBundle; "
                "storage implementation remains hidden",
            ),
        )

    if backend is ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT:
        if repositories is not None:
            raise ValueError("sqlite_test_local_vault constructs its own repository bundle")
        if not allow_test_vault:
            raise ValueError("sqlite_test_local_vault requires allow_test_vault=True")
        if vault_path is None:
            raise ValueError("sqlite_test_local_vault requires vault_path")

        from sayane.vault.sqlite_runtime import build_sqlite_test_vault_runtime

        vault_runtime = build_sqlite_test_vault_runtime(
            path=vault_path,
            profile_id=profile_id,
        )
        return ResidentRepositorySelection(
            backend=backend,
            repositories=cast(RepositoryBundle, vault_runtime.repositories),
            storage_boundary="sqlite_test_local_vault",
            vault_runtime=vault_runtime,
            notes=(
                "explicit test-only SQLite Local Vault runtime; "
                "not production auth or keychain",
            ),
        )

    if backend is ResidentRepositoryBackend.FUTURE_PRO_BACKEND:
        raise NotImplementedError(
            "future_pro_backend is reserved behind the RepositoryBundle seam",
        )

    raise AssertionError(f"unhandled resident repository backend: {backend}")


def build_resident_runtime(
    *,
    home: Path | None = None,
    host: str = "127.0.0.1",
    port: int = 38741,
    profile_id: str = "default",
    repositories: RepositoryBundle | None = None,
    repository_backend: ResidentRepositoryBackend | str | None = None,
    vault_path: Path | None = None,
    allow_test_vault: bool = False,
) -> ResidentRuntime:
    """Build a local resident runtime boundary.

    Repository backend selection is centralized here. Callers may either inject
    a RepositoryBundle or select an explicit runtime backend; entrypoints should
    not import storage implementations directly.
    """
    repository_selection = select_resident_repositories(
        profile_id=profile_id,
        repository_backend=repository_backend,
        repositories=repositories,
        vault_path=vault_path,
        allow_test_vault=allow_test_vault,
    )
    bridge_config = BridgeConfig(
        host=host,
        port=port,
        home=home or BridgeConfig().home,
    )
    service = ResidentAppService(
        profile_id=profile_id,
        repositories=repository_selection.repositories,
    )
    capabilities = {
        "capture": create_local_capability_token(["capture"]),
        "admin": create_local_capability_token(["admin"]),
    }
    return ResidentRuntime(
        service=service,
        bridge_config=bridge_config,
        repository_selection=repository_selection,
        capabilities=capabilities,
    )
