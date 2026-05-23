"""Storage backend configuration (~/.omomuki/config.yaml)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from omomuki.cli.paths import omomuki_home

DEFAULT_BACKEND = "filesystem"
DEFAULT_PROFILE_ID = "default"
CONFIG_FILENAME = "config.yaml"


@dataclass(frozen=True)
class StorageConfig:
    """Resolved storage settings for a profile store."""

    backend: str = DEFAULT_BACKEND
    profile_id: str = DEFAULT_PROFILE_ID

    @property
    def uses_git_auto_commit(self) -> bool:
        """Git auto-commit applies to filesystem backend only (until encrypted SQLite)."""
        return self.backend == DEFAULT_BACKEND


def config_path(home: Path | None = None) -> Path:
    return (home or omomuki_home()) / CONFIG_FILENAME


def load_storage_config(home: Path | None = None) -> StorageConfig:
    """Load storage config from disk; return defaults when missing."""
    path = config_path(home)
    if not path.is_file():
        return StorageConfig()
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        return StorageConfig()
    storage = raw.get("storage")
    if not isinstance(storage, dict):
        return StorageConfig()
    backend = storage.get("backend", DEFAULT_BACKEND)
    profile_id = storage.get("profile", DEFAULT_PROFILE_ID)
    if not isinstance(backend, str) or not backend.strip():
        backend = DEFAULT_BACKEND
    if not isinstance(profile_id, str) or not profile_id.strip():
        profile_id = DEFAULT_PROFILE_ID
    return StorageConfig(backend=backend.strip(), profile_id=profile_id.strip())


def save_storage_config(
    config: StorageConfig,
    *,
    home: Path | None = None,
) -> Path:
    """Persist storage config to ~/.omomuki/config.yaml."""
    path = config_path(home)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "storage": {
            "backend": config.backend,
            "profile": config.profile_id,
        },
    }
    path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return path


def profile_dir_for_id(profile_id: str, home: Path | None = None) -> Path:
    return (home or omomuki_home()) / "profiles" / profile_id
