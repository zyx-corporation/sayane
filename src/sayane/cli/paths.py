"""Default Sayane profile store paths."""

from __future__ import annotations

import os
from pathlib import Path

SAYANE_DIR_ENV = "SAYANE_DIR"


def sayane_home() -> Path:
    """Return the Sayane managed directory.

    Defaults to ~/.sayane, but can be overridden with SAYANE_DIR so profile,
    prompt, and E2E state can live under one explicit root.
    """
    raw = os.environ.get(SAYANE_DIR_ENV, "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return Path.home() / ".sayane"


def default_profile_dir() -> Path:
    return sayane_home() / "profiles" / "default"


def default_profile_file() -> Path:
    return default_profile_dir() / "sayane.profile.yaml"


def context_dir() -> Path:
    return default_profile_dir() / "context"


def prompts_dir() -> Path:
    return sayane_home() / "prompts"


def target_prompts_dir() -> Path:
    return prompts_dir() / "targets"


def model_prompts_dir() -> Path:
    return prompts_dir() / "models"


def provider_prompts_dir() -> Path:
    return prompts_dir() / "providers"


def e2e_dir() -> Path:
    return sayane_home() / "e2e"


def e2e_user_data_dir() -> Path:
    return e2e_dir() / "user-data"


def e2e_prompts_dir() -> Path:
    return e2e_dir() / "prompts"


def resolve_profile_path(profile: Path | None) -> Path:
    """Resolve profile file path; default to SAYANE_DIR or ~/.sayane store."""
    return profile if profile is not None else default_profile_file()
