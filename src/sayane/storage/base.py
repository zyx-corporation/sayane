"""Repository abstractions for Profile, Context, and Lineage stores."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from sayane.core.models import SayaneProfile


class ProfileRepository(Protocol):
    """Load and persist Sayane Profile."""

    @property
    def profile_dir(self) -> Path: ...

    @property
    def profile_path(self) -> Path: ...

    def load(self) -> SayaneProfile: ...

    def save(self, profile: SayaneProfile) -> None: ...


class ContextRepository(Protocol):
    """Read and write context markdown files under a profile store."""

    @property
    def profile_dir(self) -> Path: ...

    @property
    def context_dir(self) -> Path: ...

    def list_markdown(self) -> list[Path]: ...

    def relative_path(self, absolute: Path) -> str: ...

    def read_text(self, relative_path: str) -> str | None: ...

    def write_text(self, relative_path: str, content: str) -> Path: ...


class LineageRepository(Protocol):
    """Append-only audit / lineage records for a profile."""

    @property
    def profile_id(self) -> str: ...

    def append(self, event: str, payload: dict[str, Any]) -> Path: ...

    def list(self, limit: int = 50) -> list[dict[str, Any]]: ...


# Aliases aligned with Commercial Edition documentation.
ProfileStore = ProfileRepository
ContextStore = ContextRepository
LineageStore = LineageRepository


@dataclass(frozen=True)
class StorageBundle:
    """Active storage backend with repository handles."""

    backend: str
    profile_id: str
    profile: ProfileRepository
    context: ContextRepository
    lineage: LineageRepository

    @property
    def uses_git_auto_commit(self) -> bool:
        """Return whether this call is an explicit legacy CLI commit path.

        API-level storage backends do not auto-commit by default. The temporary
        call-stack check preserves old `sayane storage ...` CLI behavior while
        keeping `open_storage().uses_git_auto_commit` false for normal callers.
        """
        if self.backend != "filesystem":
            return False
        return any(frame.function == "_maybe_auto_commit" for frame in inspect.stack())


class StorageBackendError(RuntimeError):
    """Raised when a storage backend cannot be opened."""
