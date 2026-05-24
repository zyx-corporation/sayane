"""FileSystem storage backend (Community Edition default)."""

from __future__ import annotations

from pathlib import Path

from sayane.storage.base import StorageBundle
from sayane.storage.config import StorageConfig, profile_dir_for_id
from sayane.storage.filesystem import FileSystemContextStore, FileSystemProfileStore

BACKEND_NAME = "filesystem"


def create_backend(
    storage_config: StorageConfig,
    *,
    home: Path | None = None,
    profile_dir: Path | None = None,
) -> StorageBundle:
    """Open a filesystem-backed profile store."""
    resolved_home = home
    from sayane.cli.paths import sayane_home

    if resolved_home is None:
        resolved_home = sayane_home()
    if profile_dir is None:
        profile_dir = profile_dir_for_id(storage_config.profile_id, resolved_home)
    profile_dir = profile_dir.resolve()
    from sayane.bridge.config import BridgeConfig
    from sayane.storage.lineage import FileSystemLineageStore

    bridge_config = BridgeConfig(home=resolved_home)

    profile = FileSystemProfileStore(profile_dir)
    context = FileSystemContextStore(profile_dir)
    lineage = FileSystemLineageStore(bridge_config, storage_config.profile_id)
    return StorageBundle(
        backend=BACKEND_NAME,
        profile_id=storage_config.profile_id,
        profile=profile,
        context=context,
        lineage=lineage,
    )
