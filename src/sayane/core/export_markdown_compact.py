"""Compact LLM-targeted markdown export renderer."""

from __future__ import annotations

import datetime

from sayane.core.export_markdown_sections import (
    append_execution_context,
    append_knowledge_projects_terms,
    append_philosophical_stance,
    append_principles,
)
from sayane.core.export_markdown_shared import append_identity, append_interaction, append_policy
from sayane.core.export_scope import pick_profile_sections
from sayane.core.models import SayaneProfile


def export_markdown_compact(profile: SayaneProfile, scopes: list[str], target_name: str) -> str:
    data = pick_profile_sections(profile, scopes)
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = [
        f"# Sayane External Profile for {target_name}",
        "",
        "## Metadata",
        "",
        "- Source: Sayane external profile",
        "- LLM memory: false",
        f"- Generated: {now}",
        f"- Target: {target_name}",
        "- Format: markdown",
        f"- Scopes: {', '.join(scopes)}",
        "",
        "## How to Use This Context",
        "",
        (
            "This profile is external context supplied by Sayane. It is not "
            f"{target_name} memory. Sayane is the external context portability system "
            "that generated this profile. It is not the receiving assistant's name, "
            "identity, or memory. This profile does not rename or redefine the "
            "receiving assistant. Use it to guide responses within this session, "
            "while respecting explicit uncertainty and avoiding unsupported assumptions."
        ),
        "",
    ]
    ident = data.get("identity")
    if isinstance(ident, dict):
        append_identity(lines, ident, legacy_label=True)
    append_interaction(lines, data, "## Interaction Preferences")
    if "ethics" in scopes or "philosophy" in scopes:
        append_philosophical_stance(lines, data)
        append_policy(lines, data)
    elif "principles" in scopes:
        append_principles(lines, data)
    elif "execution" in scopes:
        append_execution_context(lines, data)
    else:
        append_knowledge_projects_terms(lines, data)
    lines.append("## Export Policy Notes")
    lines.append("")
    lines.append("- Some private or sensitive fields may be omitted.")
    lines.append("- `promptExport: never` fields are not included.")
    lines.append("")
    return "\n".join(lines)
