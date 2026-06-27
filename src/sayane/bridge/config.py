"""Local Bridge configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

from sayane.cli.paths import sayane_home

if TYPE_CHECKING:
    from sayane.storage.repositories import RepositoryBundle


@dataclass
class BridgeConfig:
    """Runtime configuration for the Local Bridge."""

    host: str = "127.0.0.1"
    port: int = 38741
    home: Path = field(default_factory=sayane_home)
    ui_session_ttl_seconds: int = 12 * 60 * 60
    repositories: "RepositoryBundle | None" = None
    repository_session: Any | None = None

    @property
    def token_file(self) -> Path:
        return self.home / "bridge.token"

    @property
    def ui_session_file(self) -> Path:
        return self.home / "bridge.ui-session.json"

    @property
    def profiles_dir(self) -> Path:
        return self.home / "profiles"

    @property
    def candidates_dir(self) -> Path:
        return self.home / "candidates"

    def repository_kwargs(self) -> dict[str, Any]:
        if self.repository_session is None:
            return {}
        return {"session": self.repository_session}
