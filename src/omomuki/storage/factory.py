"""Open the configured storage backend for a profile."""

from __future__ import annotations

from pathlib import Path

from omomuki.cli.paths import omomuki_home, resolve_profile_path
from omomuki.storage.base import StorageBackendError, StorageBundle
from omomuki.storage.config import (
    StorageConfig,
    load_storage_config,
    profile_dir_for_id,
    save_storage_config,
)
from omomuki.storage.registry import get_backend_factory, list_backends, open_backend


def open_storage(
    *,
    profile: Path | None = None,
    profile_id: str | None = None,
    home: Path | None = None,
    storage_config: StorageConfig | None = None,
) -> StorageBundle:
    """Open repositories for the active storage backend."""
    resolved_home = home or omomuki_home()
    config = storage_config or load_storage_config(resolved_home)
    if profile_id is not None:
        config = StorageConfig(backend=config.backend, profile_id=profile_id)

    profile_dir: Path | None = None
    if profile is not None:
        profile_path = resolve_profile_path(profile)
        if not profile_path.exists():
            raise StorageBackendError(f"Profile not found: {profile_path}")
        profile_dir = profile_path.parent.resolve()
        inferred_id = profile_dir.name
        config = StorageConfig(backend=config.backend, profile_id=inferred_id)
    else:
        profile_dir = profile_dir_for_id(config.profile_id, resolved_home)
        profile_path = profile_dir / "omomuki.profile.yaml"
        if config.backend == "filesystem" and not profile_path.exists():
            raise StorageBackendError(f"Profile not found: {profile_path}")

    return open_backend(config, home=resolved_home, profile_dir=profile_dir)


def set_storage_backend(
    backend: str,
    *,
    home: Path | None = None,
    profile_id: str | None = None,
) -> StorageConfig:
    """Validate and persist a storage backend selection."""
    get_backend_factory(backend)  # raises if unknown
    current = load_storage_config(home)
    updated = StorageConfig(
        backend=backend,
        profile_id=profile_id or current.profile_id,
    )
    save_storage_config(updated, home=home)
    return updated


__all__ = [
    "list_backends",
    "open_storage",
    "set_storage_backend",
]
