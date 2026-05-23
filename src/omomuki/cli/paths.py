"""Default Omomuki profile store paths."""

from pathlib import Path


def omomuki_home() -> Path:
    return Path.home() / ".omomuki"


def default_profile_dir() -> Path:
    return omomuki_home() / "profiles" / "default"


def default_profile_file() -> Path:
    return default_profile_dir() / "omomuki.profile.yaml"


def context_dir() -> Path:
    return default_profile_dir() / "context"


def resolve_profile_path(profile: Path | None) -> Path:
    """Resolve profile file path; default to ~/.omomuki store."""
    return profile if profile is not None else default_profile_file()
