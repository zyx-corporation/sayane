"""Prompt export renderer."""

from __future__ import annotations

from sayane.core.export_markdown_sections import append_knowledge_projects_terms
from sayane.core.export_markdown_shared import append_policy
from sayane.core.export_scope import pick_profile_sections
from sayane.core.models import SayaneProfile


def export_prompt(profile: SayaneProfile, scopes: list[str], target: str = "generic") -> str:
    del target
    data = pick_profile_sections(profile, scopes)
    lines: list[str] = ["[Context]", ""]
    ident = data.get("identity")
    if isinstance(ident, dict):
        if ident.get("name"):
            lines.append(f"You are interacting with: {ident['name']}")
        if ident.get("preferred_name"):
            lines.append(f"Use preferred form of address: {ident['preferred_name']}")
        roles = ident.get("roles", [])
        if roles:
            lines.append(f"Roles: {', '.join(roles)}")
    voice = data.get("voice")
    cm = data.get("communication_mode")
    if isinstance(voice, dict) or isinstance(cm, dict):
        lines.append("")
        if isinstance(voice, dict):
            if voice.get("default_language"):
                lines.append(f"Language: {voice['default_language']}")
            tone = voice.get("tone", [])
            if tone:
                lines.append(f"Tone: {', '.join(tone)}")
        if isinstance(cm, dict):
            styles = cm.get("collaboration_style", [])
            if styles:
                lines.append(f"Collaboration: {', '.join(styles)}")
    values = data.get("values")
    if isinstance(values, dict) and values.get("core"):
        lines.append("")
        lines.append("Values:")
        for value in values["core"]:
            lines.append(f"- {value}")
    append_policy(lines, data)
    append_knowledge_projects_terms(lines, data)
    return "\n".join(lines)
