"""Profile and lineage storage abstractions."""

from omomuki.storage.base import (
    ContextRepository,
    ContextStore,
    LineageRepository,
    LineageStore,
    ProfileRepository,
    ProfileStore,
    StorageBackendError,
    StorageBundle,
)
from omomuki.storage.config import StorageConfig, load_storage_config

__all__ = [
    "ContextRepository",
    "ContextStore",
    "LineageRepository",
    "LineageStore",
    "ProfileRepository",
    "ProfileStore",
    "StorageBackendError",
    "StorageBundle",
    "StorageConfig",
    "list_backends",
    "load_storage_config",
    "open_storage",
    "set_storage_backend",
]


def __getattr__(name: str):
    if name == "open_storage":
        from omomuki.storage.factory import open_storage as fn

        return fn
    if name == "set_storage_backend":
        from omomuki.storage.factory import set_storage_backend as fn

        return fn
    if name == "list_backends":
        from omomuki.storage.registry import list_backends as fn

        return fn
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
