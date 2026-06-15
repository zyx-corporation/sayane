"""Generic markdown export renderer."""

from __future__ import annotations

from sayane.core.export_markdown_sections import append_knowledge_projects_terms
from sayane.core.export_markdown_shared import (
    append_identity,
    append_interaction,
    append_values_and_policy,
)
from sayane.core.export_scope import pick_profile_sections
from sayane.core.models import SayaneProfile


def export_markdown_generic(profile: SayaneProfile, scopes: list[str], target: str) -> str:
    data = pick_profile_sections(profile, scopes)
    lines: list[str] = ["# Sayane Context Bundle", "", f"Target: {target}", f"Scopes: {', '.join(scopes)}", ""]
    ident = data.get("identity")
    if isinstance(ident, dict):
        append_identity(lines, ident, legacy_label=False)
    append_interaction(lines, data, "## Interaction Style")
    append_values_and_policy(lines, data)
    append_knowledge_projects_terms(lines, data)
    return "\n".join(lines)
