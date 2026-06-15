"""Shared markdown renderer helpers for context export."""

from __future__ import annotations

from typing import Any


def append_identity(lines: list[str], ident: dict[str, Any], *, legacy_label: bool) -> None:
    lines.append("## Identity")
    lines.append("")
    if legacy_label:
        lines.append("Identity:")
    if ident.get("name"):
        lines.append(f"- Name: {ident['name']}")
    if ident.get("preferred_name"):
        lines.append(f"- Preferred name: {ident['preferred_name']}")
    roles = ident.get("roles", [])
    if roles:
        lines.append(f"- Roles: {', '.join(roles)}")
    lines.append("")


def append_interaction(lines: list[str], data: dict[str, Any], heading: str) -> None:
    voice = data.get("voice")
    cm = data.get("communication_mode")
    if not isinstance(voice, dict) and not isinstance(cm, dict):
        return
    lines.append(heading)
    lines.append("")
    if isinstance(voice, dict):
        if voice.get("default_language"):
            lines.append(f"- Language: {voice['default_language']}")
        tone = voice.get("tone", [])
        if tone:
            lines.append(f"- Tone: {', '.join(tone)}")
    if isinstance(cm, dict):
        if cm.get("assistant_name_for_chatgpt"):
            lines.append(f"- Assistant name: {cm['assistant_name_for_chatgpt']}")
        if cm.get("preferred_address"):
            lines.append(f"- Preferred address: {cm['preferred_address']}")
        styles = cm.get("collaboration_style", [])
        if styles:
            lines.append(f"- Collaboration style: {', '.join(styles)}")
    lines.append("")


def append_policy(lines: list[str], data: dict[str, Any]) -> None:
    policy = data.get("policy")
    if not isinstance(policy, dict):
        return
    response = policy.get("response")
    if not isinstance(response, dict):
        return
    prefer = response.get("prefer", [])
    avoid = response.get("avoid", [])
    if not prefer and not avoid:
        return
    lines.append("## Response Policy")
    lines.append("")
    if prefer:
        lines.append("Prefer:")
        for item in prefer:
            lines.append(f"- {item}")
    if avoid:
        lines.append("Avoid:")
        for item in avoid:
            lines.append(f"- {item}")
    lines.append("")


def append_values_and_policy(lines: list[str], data: dict[str, Any]) -> None:
    values = data.get("values")
    if isinstance(values, dict) and values.get("core"):
        lines.append("## Values")
        lines.append("")
        for value in values["core"]:
            lines.append(f"- {value}")
        lines.append("")
    append_policy(lines, data)
