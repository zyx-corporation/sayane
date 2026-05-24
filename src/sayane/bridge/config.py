"""Local Bridge configuration."""

from dataclasses import dataclass, field
from pathlib import Path

from sayane.cli.paths import sayane_home


@dataclass
class BridgeConfig:
    """Runtime configuration for the Local Bridge."""

    host: str = "127.0.0.1"
    port: int = 38741
    home: Path = field(default_factory=sayane_home)

    @property
    def token_file(self) -> Path:
        return self.home / "bridge.token"

    @property
    def profiles_dir(self) -> Path:
        return self.home / "profiles"

    @property
    def candidates_dir(self) -> Path:
        return self.home / "candidates"
