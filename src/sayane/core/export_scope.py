"""Export scope selection and section mapping."""

from __future__ import annotations

from typing import Any

from sayane.core.export_noise import clean_export_data
from sayane.core.models import SayaneProfile

SCOPE_SECTIONS: dict[str, list[str]] = {
    "identity": ["identity"],
    "interaction": ["voice", "communication_mode"],
    "writing": ["voice"],
    "technical": ["knowledge"],
    "projects": ["major_projects"],
    "ethics": ["values", "policy"],
    "formation": ["identity", "values"],
    "important_terms": ["important_terms"],
    "philosophy": ["values"],
    "principles": ["knowledge"],
    "execution": ["major_projects", "communication_mode"],
}


def pick_profile_sections(profile: SayaneProfile, scopes: list[str]) -> dict[str, Any]:
    keys: set[str] = set()
    for scope in scopes:
        sections = SCOPE_SECTIONS.get(scope.strip().lower())
        if sections:
            keys.update(sections)
    profile_dict = profile.model_dump(mode="json")
    raw = {key: value for key, value in profile_dict.items() if key in keys and value is not None}
    return clean_export_data(raw)
