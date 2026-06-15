"""YAML export renderer."""

from __future__ import annotations

import yaml

from sayane.core.export_scope import pick_profile_sections
from sayane.core.models import SayaneProfile


def export_yaml(profile: SayaneProfile, scopes: list[str]) -> str:
    data = pick_profile_sections(profile, scopes)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
