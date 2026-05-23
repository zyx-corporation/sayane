"""Load Omomuki Profile from YAML files."""

from pathlib import Path

import yaml

from omomuki.core.models import OmomukiProfile


def load_profile(path: Path) -> OmomukiProfile:
    """Load and validate a profile from a YAML file."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return OmomukiProfile.model_validate(data)


def save_profile(path: Path, profile: OmomukiProfile) -> None:
    """Write profile to YAML."""
    data = profile.model_dump(mode="json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
