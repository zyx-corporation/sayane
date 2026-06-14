"""Tests for storage backend plugin contract."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from sayane.core.models import SayaneProfile
from sayane.storage.base import StorageBackendError, StorageBundle
from sayane.storage.config import StorageConfig, load_storage_config, save_storage_config
from sayane.storage.factory import open_storage, set_storage_backend
from sayane.storage.git_integration import legacy_git_autocommit_enabled
from sayane.storage.registry import (
    get_backend_factory,
    list_backends,
    register_backend,
    reset_discovery,
    unregister_backend,
)


@dataclass
class _MemoryProfileRepo:
    profile_dir: Path
    profile_path: Path
    _profile: SayaneProfile | None = None

    def load(self) -> SayaneProfile:
        if self._profile is None:
            raise FileNotFoundError(self.profile_path)
        return self._profile

    def save(self, profile: SayaneProfile) -> None:
        self._profile = profile


@dataclass
class _MemoryContextRepo:
    profile_dir: Path
    context_dir: Path
    files: dict[str, str]

    def list_markdown(self) -> list[Path]:
        return sorted(self.context_dir.glob("**/*.md"))

    def relative_path(self, absolute: Path) -> str:
        return absolute.relative_to(self.context_dir).as_posix()

    def read_text(self, relative_path: str) -> str | None:
        return self.files.get(relative_path)

    def write_text(self, relative_path: str, content: str) -> Path:
        path = self.context_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        self.files[relative_path] = content
        return path


@dataclass
class _MemoryLineageRepo:
    profile_id: str
    records: list[dict[str, Any]]

    def append(self, event: str, payload: dict[str, Any]) -> Path:
        self.records.append({"event": event, **payload})
        return Path(f"/dev/null/{event}")

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.records[-limit:]


def _memory_backend_factory(
    storage_config: StorageConfig,
    *,
    home: Path | None = None,
    profile_dir: Path | None = None,
) -> StorageBundle:
    root = profile_dir or (home or Path("/tmp")) / "profiles" / storage_config.profile_id
    root.mkdir(parents=True, exist_ok=True)
    context_dir = root / "context"
    context_dir.mkdir(exist_ok=True)
    profile_path = root / "sayane.profile.yaml"
    return StorageBundle(
        backend="memory",
        profile_id=storage_config.profile_id,
        profile=_MemoryProfileRepo(root, profile_path),
        context=_MemoryContextRepo(root, context_dir, {}),
        lineage=_MemoryLineageRepo(storage_config.profile_id, []),
    )


@pytest.fixture(autouse=True)
def _reset_registry() -> None:
    reset_discovery()
    yield
    reset_discovery()


def test_load_storage_config_defaults(tmp_path: Path) -> None:
    config = load_storage_config(tmp_path)
    assert config.backend == "filesystem"
    assert config.profile_id == "default"
    assert config.uses_git_auto_commit is False


def test_save_and_load_storage_config(tmp_path: Path) -> None:
    save_storage_config(StorageConfig(backend="filesystem", profile_id="work"), home=tmp_path)
    loaded = load_storage_config(tmp_path)
    assert loaded.backend == "filesystem"
    assert loaded.profile_id == "work"
    assert loaded.uses_git_auto_commit is False


def test_filesystem_backend_open_storage(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    profile_dir = home / "profiles" / "default"
    profile_dir.mkdir(parents=True)
    (profile_dir / "sayane.profile.yaml").write_text(
        'version: "0.1.0"\nkind: SayaneProfile\nidentity:\n  name: "Test"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("sayane.storage.factory.sayane_home", lambda: home)

    bundle = open_storage(home=home)
    assert bundle.backend == "filesystem"
    assert bundle.profile.profile_dir == profile_dir.resolve()
    assert bundle.context.context_dir == profile_dir.resolve() / "context"
    assert bundle.uses_git_auto_commit is False


def test_legacy_git_auto_commit_requires_explicit_opt_in(monkeypatch) -> None:
    monkeypatch.delenv("SAYANE_ENABLE_LEGACY_GIT_AUTOCOMMIT", raising=False)
    assert legacy_git_autocommit_enabled() is False
    monkeypatch.setenv("SAYANE_ENABLE_LEGACY_GIT_AUTOCOMMIT", "1")
    assert legacy_git_autocommit_enabled() is True


def test_mock_backend_registration_contract(tmp_path: Path) -> None:
    register_backend("memory", _memory_backend_factory)
    assert "memory" in list_backends()
    factory = get_backend_factory("memory")
    bundle = factory(StorageConfig(backend="memory", profile_id="default"), home=tmp_path)
    assert bundle.backend == "memory"
    assert bundle.profile_id == "default"


def test_unknown_backend_raises() -> None:
    with pytest.raises(StorageBackendError, match="encrypted-sqlite"):
        get_backend_factory("encrypted-sqlite")


def test_set_storage_backend_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("sayane.storage.factory.sayane_home", lambda: tmp_path)
    config = set_storage_backend("filesystem", home=tmp_path)
    assert config.backend == "filesystem"
    assert load_storage_config(tmp_path).backend == "filesystem"


def test_storage_backend_status_cli(tmp_path: Path, monkeypatch) -> None:
    from typer.testing import CliRunner

    from sayane.cli.app import build_app

    home = tmp_path / "home"
    profile_dir = home / "profiles" / "default"
    profile_dir.mkdir(parents=True)
    (profile_dir / "sayane.profile.yaml").write_text(
        'version: "0.1.0"\nkind: SayaneProfile\nidentity:\n  name: "Test"\n',
        encoding="utf-8",
    )
    monkeypatch.setattr("sayane.storage.factory.sayane_home", lambda: home)

    runner = CliRunner()
    result = runner.invoke(build_app(), ["storage", "backend", "status"])
    assert result.exit_code == 0
    assert "filesystem" in result.stdout


def test_unregister_backend(tmp_path: Path) -> None:
    register_backend("memory", _memory_backend_factory)
    unregister_backend("memory")
    with pytest.raises(StorageBackendError):
        get_backend_factory("memory")
