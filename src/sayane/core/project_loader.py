"""Load optional Sayane Project Profile from a profile directory."""

from pathlib import Path

import yaml

from sayane.core.models import SayaneProjectProfile

PROJECT_PROFILE_FILENAME = "sayane.project.yaml"


def load_project_profile(profile_root: Path) -> SayaneProjectProfile | None:
    """Load project profile if ``sayane.project.yaml`` exists."""
    path = profile_root / PROJECT_PROFILE_FILENAME
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return SayaneProjectProfile.model_validate(data)
