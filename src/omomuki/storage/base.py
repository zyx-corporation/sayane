"""Repository abstractions for Profile, Context, and Lineage stores."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from omomuki.core.models import OmomukiProfile


class ProfileRepository(Protocol):
    """Load and persist Omomuki Profile."""

    @property
    def profile_dir(self) -> Path: ...

    @property
    def profile_path(self) -> Path: ...

    def load(self) -> OmomukiProfile: ...

    def save(self, profile: OmomukiProfile) -> None: ...


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
        return self.backend == "filesystem"


class StorageBackendError(RuntimeError):
    """Raised when a storage backend cannot be opened."""
