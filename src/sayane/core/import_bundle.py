"""Import portable context bundles as reviewable Candidates (#143)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from sayane.core.models import SayaneProfile
from sayane.core.export import SCOPE_SECTIONS


def parse_bundle(path: Path) -> dict[str, Any] | None:
    """Parse a portable context bundle (YAML or Markdown)."""
    text = path.read_text(encoding="utf-8")
    if text.strip().startswith("{"):
        # JSON
        import json
        return json.loads(text)
    if text.strip().startswith("#"):
        # Markdown: extract YAML frontmatter or parse sections
        return _parse_markdown_bundle(text)
    # YAML
    try:
        return yaml.safe_load(text) or {}
    except yaml.YAMLError:
        return None


def _parse_markdown_bundle(text: str) -> dict[str, Any]:
    """Extract key-value pairs from markdown sections for import."""
    result: dict[str, Any] = {}
    current_section: str | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("## "):
            current_section = stripped[3:].strip().lower()
            continue
        if stripped.startswith("- ") and current_section:
            value = stripped[2:].strip()
            if current_section == "identity":
                if "identity" not in result:
                    result["identity"] = {}
                if value.startswith("Name: "):
                    result["identity"]["name"] = value[6:]
                elif value.startswith("Preferred name: "):
                    result["identity"]["preferred_name"] = value[16:]
                elif value.startswith("Roles: "):
                    result["identity"]["roles"] = [r.strip() for r in value[7:].split(",")]
            elif current_section in ("key concepts", "important terms"):
                key = "knowledge" if current_section == "key concepts" else "important_terms"
                result.setdefault(key, []).append(value)
    return result


_IMPORTABLE_SECTIONS = frozenset({
    "identity",
    "voice",
    "communication_mode",
    "values",
    "knowledge",
    "policy",
    "major_projects",
    "important_terms",
})


def import_bundle_as_candidates(
    bundle: dict[str, Any],
    profile: SayaneProfile,
) -> list[dict[str, Any]]:
    """Compare bundle sections against stored profile and return candidate drafts.

    Each returned dict has:
    - section: target profile section
    - current_value: value from profile (None if new)
    - proposed_value: value from bundle
    - action: 'add' | 'update' | 'unchanged'
    """
    candidates: list[dict[str, Any]] = []
    profile_dict = profile.model_dump(mode="json")

    for key in bundle:
        if key not in _IMPORTABLE_SECTIONS:
            continue
        proposed = bundle[key]
        existing = profile_dict.get(key)

        if existing is None and proposed:
            candidates.append({
                "section": key,
                "current_value": None,
                "proposed_value": proposed,
                "action": "add",
            })
        elif isinstance(existing, list) and isinstance(proposed, list):
            # List sections: diff
            existing_set = {str(v).strip().lower() if isinstance(v, str) else str(v) for v in existing}
            add = [v for v in proposed if str(v).strip().lower() not in existing_set]
            if add:
                candidates.append({
                    "section": key,
                    "current_value": existing,
                    "proposed_value": add,
                    "action": "add",
                })
        elif isinstance(existing, dict) and isinstance(proposed, dict):
            # Dict sections: merge check
            diff: dict[str, Any] = {}
            for k, v in proposed.items():
                if k not in existing or existing[k] != v:
                    diff[k] = v
            if diff:
                candidates.append({
                    "section": key,
                    "current_value": existing,
                    "proposed_value": diff,
                    "action": "update",
                })
        elif existing != proposed:
            candidates.append({
                "section": key,
                "current_value": existing,
                "proposed_value": proposed,
                "action": "update",
            })

    return candidates
