"""FileSystem storage backend (Community Edition default)."""

from __future__ import annotations

from pathlib import Path

from omomuki.storage.base import StorageBundle
from omomuki.storage.config import StorageConfig, profile_dir_for_id
from omomuki.storage.filesystem import FileSystemContextStore, FileSystemProfileStore

BACKEND_NAME = "filesystem"


def create_backend(
    storage_config: StorageConfig,
    *,
    home: Path | None = None,
    profile_dir: Path | None = None,
) -> StorageBundle:
    """Open a filesystem-backed profile store."""
    resolved_home = home
    from omomuki.cli.paths import omomuki_home

    if resolved_home is None:
        resolved_home = omomuki_home()
    if profile_dir is None:
        profile_dir = profile_dir_for_id(storage_config.profile_id, resolved_home)
    profile_dir = profile_dir.resolve()
    from omomuki.bridge.config import BridgeConfig
    from omomuki.storage.lineage import FileSystemLineageStore

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
