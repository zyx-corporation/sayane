"""Default Sayane profile store paths."""

from pathlib import Path


def sayane_home() -> Path:
    return Path.home() / ".sayane"


def default_profile_dir() -> Path:
    return sayane_home() / "profiles" / "default"


def default_profile_file() -> Path:
    return default_profile_dir() / "sayane.profile.yaml"


def context_dir() -> Path:
    return default_profile_dir() / "context"


def resolve_profile_path(profile: Path | None) -> Path:
    """Resolve profile file path; default to ~/.sayane store."""
    return profile if profile is not None else default_profile_file()
