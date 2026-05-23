"""Repository abstractions for Profile and Context stores."""

from pathlib import Path
from typing import Protocol

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
    def context_dir(self) -> Path: ...

    def list_markdown(self) -> list[Path]: ...

    def read_text(self, relative_path: str) -> str | None: ...

    def write_text(self, relative_path: str, content: str) -> Path: ...
