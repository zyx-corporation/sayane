"""Capture-time previews (no Candidate persistence)."""

from __future__ import annotations

from sayane.bridge.config import BridgeConfig
from sayane.bridge.service import resolve_profile_path
from sayane.core.loader import load_profile
from sayane.evaluators.list_diff import (
    important_terms_profile_diff,
    parse_yaml_list_section,
)


def preview_important_terms_diff(
    config: BridgeConfig,
    *,
    profile_id: str,
    content: str,
) -> dict[str, int | str]:
    """Compare clipboard YAML to saved profile.important_terms only."""
    proposed = parse_yaml_list_section(content.strip(), "important_terms")
    if not proposed:
        raise ValueError("No important_terms list found in content")

    profile = load_profile(resolve_profile_path(config, profile_id))
    existing = list(profile.important_terms or [])
    diff = important_terms_profile_diff(existing, proposed)

    return {
        "section": "important_terms",
        "total": len(proposed),
        "existing_count": diff.unchanged_count,
        "added_count": len(diff.added),
        "removed_count": len(diff.removed),
    }
