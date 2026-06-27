"""CLI helpers for vault-aware BridgeConfig resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import typer

from sayane.app.runtime import ResidentRepositoryBackend, build_resident_runtime
from sayane.bridge.config import BridgeConfig
from sayane.vault.unlock_policy import UnlockLevel

CliVaultMode = Literal["test", "development", "macos-keychain"]


def resolve_cli_bridge_config(
    *,
    vault_mode: CliVaultMode | None = None,
    vault_sqlite: Path | None = None,
    unlock_level: UnlockLevel | None = None,
    unlock_purpose: str = "cli-command",
    profile_id: str = "default",
) -> BridgeConfig:
    """Return BridgeConfig, optionally backed by an explicit Local Vault runtime."""
    cfg = BridgeConfig()
    if vault_mode is None:
        return cfg

    backend_map: dict[CliVaultMode, ResidentRepositoryBackend] = {
        "test": ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT,
        "development": ResidentRepositoryBackend.SQLITE_DEVELOPMENT_LOCAL_VAULT,
        "macos-keychain": ResidentRepositoryBackend.SQLITE_MACOS_KEYCHAIN_VAULT,
    }
    default_name = "test.sqlite" if vault_mode == "test" else "main.sqlite"
    resolved_vault_path = vault_sqlite or (cfg.home / "vault" / default_name)
    runtime = build_resident_runtime(
        home=cfg.home,
        host=cfg.host,
        port=cfg.port,
        profile_id=profile_id,
        repository_backend=backend_map[vault_mode],
        vault_path=resolved_vault_path,
        allow_test_vault=(vault_mode == "test"),
    )
    repository_session = None
    if runtime.vault_runtime is not None:
        level = unlock_level or UnlockLevel.SENSITIVE
        try:
            repository_session = runtime.vault_runtime.open_policy_session(
                unlock_purpose,
                level,
            )
        except Exception as exc:
            raise typer.BadParameter(str(exc)) from exc

    return BridgeConfig(
        host=cfg.host,
        port=cfg.port,
        home=cfg.home,
        ui_session_ttl_seconds=cfg.ui_session_ttl_seconds,
        repositories=runtime.service.repositories,
        repository_session=repository_session,
    )
