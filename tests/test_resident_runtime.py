"""Tests for resident runtime builder (#180, #184)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app.runtime import (
    ResidentRepositoryBackend,
    ResidentRuntime,
    build_resident_runtime,
    select_resident_repositories,
)
from sayane.storage.repositories import build_test_repository_bundle


def test_resident_runtime_describes_service_and_bridge_config(tmp_path) -> None:
    runtime = build_resident_runtime(
        home=tmp_path / "sayane",
        host="127.0.0.1",
        port=39000,
    )

    assert isinstance(runtime, ResidentRuntime)
    assert runtime.bridge_config.home == tmp_path / "sayane"
    assert runtime.bridge_config.host == "127.0.0.1"
    assert runtime.bridge_config.port == 39000
    assert runtime.describe() == {
        "profile_id": "default",
        "has_repositories": False,
        "candidate_repository": False,
        "review_decision_repository": False,
        "lineage_repository": False,
        "bridge_host": "127.0.0.1",
        "bridge_port": 39000,
        "capabilities": ["admin", "capture", "mcp", "ui"],
        "repository_backend": "legacy_process_local",
        "storage_boundary": "none",
        "repository_selection": {
            "backend": "legacy_process_local",
            "has_repositories": False,
            "storage_boundary": "none",
            "notes": [
                "legacy process-local fallback only; not a production durable "
                "resident state store",
            ],
        },
    }


def test_resident_runtime_accepts_explicit_repository_bundle(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    runtime = build_resident_runtime(
        home=tmp_path / "sayane",
        repositories=bundle,
    )

    assert runtime.service.repositories is bundle
    assert (
        runtime.repository_selection.backend
        is ResidentRepositoryBackend.INJECTED_REPOSITORY_BUNDLE
    )
    assert runtime.describe()["has_repositories"] is True
    assert runtime.describe()["candidate_repository"] is True
    assert runtime.describe()["repository_backend"] == "injected_repository_bundle"
    assert runtime.describe()["storage_boundary"] == "repository_bundle"


def test_resident_runtime_capabilities_are_separate() -> None:
    runtime = build_resident_runtime()

    assert runtime.capabilities["capture"].has("capture") is True
    assert runtime.capabilities["capture"].has("admin") is False
    assert runtime.capabilities["ui"].has("ui") is True
    assert runtime.capabilities["ui"].has("mcp") is False
    assert runtime.capabilities["mcp"].has("mcp") is True
    assert runtime.capabilities["mcp"].has("ui") is False
    assert runtime.capabilities["admin"].has("capture") is True
    assert runtime.capabilities["admin"].has("review") is True


def test_select_resident_repositories_rejects_unknown_backend() -> None:
    with pytest.raises(ValueError, match="Unsupported resident repository backend"):
        select_resident_repositories(repository_backend="unknown")


def test_injected_backend_requires_repository_bundle() -> None:
    with pytest.raises(ValueError, match="requires repositories"):
        select_resident_repositories(
            repository_backend=ResidentRepositoryBackend.INJECTED_REPOSITORY_BUNDLE,
        )


def test_explicit_legacy_backend_rejects_repository_bundle() -> None:
    bundle = build_test_repository_bundle(profile_id="default")

    with pytest.raises(ValueError, match="repositories require"):
        select_resident_repositories(
            repository_backend=ResidentRepositoryBackend.LEGACY_PROCESS_LOCAL,
            repositories=bundle,
        )


def test_sqlite_test_local_vault_requires_explicit_allow(tmp_path) -> None:
    with pytest.raises(ValueError, match="allow_test_vault=True"):
        build_resident_runtime(
            repository_backend=ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT,
            vault_path=tmp_path / "sayane.sqlite3",
        )


def test_sqlite_test_local_vault_requires_path() -> None:
    with pytest.raises(ValueError, match="requires vault_path"):
        build_resident_runtime(
            repository_backend=ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT,
            allow_test_vault=True,
        )


def test_sqlite_test_local_vault_selects_repository_bundle(tmp_path) -> None:
    runtime = build_resident_runtime(
        repository_backend=ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT,
        vault_path=tmp_path / "sayane.sqlite3",
        allow_test_vault=True,
    )

    assert runtime.service.repositories is not None
    assert (
        runtime.repository_selection.backend
        is ResidentRepositoryBackend.SQLITE_TEST_LOCAL_VAULT
    )
    assert runtime.describe()["has_repositories"] is True
    assert runtime.describe()["repository_backend"] == "sqlite_test_local_vault"
    assert runtime.describe()["storage_boundary"] == "sqlite_test_local_vault"


def test_resident_runtime_can_select_test_vault_from_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAYANE_APP_VAULT_MODE", "test")
    runtime = build_resident_runtime(home=tmp_path / "sayane")

    assert runtime.describe()["repository_backend"] == "sqlite_test_local_vault"
    assert runtime.describe()["has_repositories"] is True


def test_resident_runtime_can_select_development_vault_from_environment(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAYANE_APP_VAULT_MODE", "development")
    monkeypatch.setenv("SAYANE_VAULT_PASSPHRASE", "dev-passphrase")
    runtime = build_resident_runtime(home=tmp_path / "sayane")

    assert runtime.describe()["repository_backend"] == "sqlite_development_local_vault"
    assert runtime.describe()["has_repositories"] is True


def test_future_pro_backend_is_reserved() -> None:
    with pytest.raises(NotImplementedError, match="reserved"):
        build_resident_runtime(
            repository_backend=ResidentRepositoryBackend.FUTURE_PRO_BACKEND,
        )


def test_cli_does_not_import_sqlite_runtime_directly() -> None:
    cli_app = Path("src/sayane/cli/commands/app.py").read_text(encoding="utf-8")

    assert "sqlite_runtime" not in cli_app
    assert "build_sqlite_test_vault_runtime" not in cli_app
