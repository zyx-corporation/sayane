"""Load Omomuki Profile from YAML files."""

from pathlib import Path

import yaml

from omomuki.core.models import OmomukiProfile


def load_profile(path: Path) -> OmomukiProfile:
    """Load and validate a profile from a YAML file."""
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return OmomukiProfile.model_validate(data)
