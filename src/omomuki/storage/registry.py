"""Storage backend registration and discovery."""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import entry_points
from pathlib import Path

from omomuki.storage.backends import filesystem as filesystem_backend
from omomuki.storage.base import StorageBackendError, StorageBundle
from omomuki.storage.config import StorageConfig

BackendFactory = Callable[..., StorageBundle]

_BACKEND_FACTORIES: dict[str, BackendFactory] = {}


def register_backend(name: str, factory: BackendFactory) -> None:
    """Register a storage backend factory by name."""
    if not name or not name.strip():
        raise ValueError("backend name must be non-empty")
    _BACKEND_FACTORIES[name.strip()] = factory


def unregister_backend(name: str) -> None:
    _BACKEND_FACTORIES.pop(name, None)


def clear_backends() -> None:
    """Remove all registered backends (tests only)."""
    _BACKEND_FACTORIES.clear()
    _register_builtin_backends()


def list_backends() -> list[str]:
    _ensure_discovered()
    return sorted(_BACKEND_FACTORIES)


def get_backend_factory(name: str) -> BackendFactory:
    _ensure_discovered()
    try:
        return _BACKEND_FACTORIES[name]
    except KeyError as exc:
        registered = ", ".join(list_backends()) or "(none)"
        raise StorageBackendError(
            f"Storage backend '{name}' is not registered. "
            f"Available: {registered}. "
            "Install omomuki-pro for encrypted-sqlite.",
        ) from exc


def open_backend(
    storage_config: StorageConfig,
    *,
    home: Path | None = None,
    profile_dir: Path | None = None,
) -> StorageBundle:
    factory = get_backend_factory(storage_config.backend)
    return factory(storage_config, home=home, profile_dir=profile_dir)


def _register_builtin_backends() -> None:
    register_backend(filesystem_backend.BACKEND_NAME, filesystem_backend.create_backend)


def _discover_entry_points() -> None:
    try:
        eps = entry_points(group="omomuki.storage_backends")
    except TypeError:
        eps = entry_points().get("omomuki.storage_backends", ())
    for ep in eps:
        register_backend(ep.name, ep.load())


_discovered = False


def _ensure_discovered() -> None:
    global _discovered
    if _discovered:
        return
    _register_builtin_backends()
    _discover_entry_points()
    _discovered = True


def reset_discovery() -> None:
    """Reset registry state (tests only)."""
    global _discovered
    _discovered = False
    _BACKEND_FACTORIES.clear()
