"""Context Portability export: yaml / markdown / prompt with scope and policy."""

from __future__ import annotations

from typing import Any

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

_EXPORT_NOISE_SUBSTRINGS: tuple[str, ...] = (
    "Capture",
    "Candidate",
    "Popup",
    "Sayane —",
    "Side Panel",
    "Debug",
    "このフィルタ",
    "差分ビュー",
    "候補メタデータ",
    "元の文脈",
    "候補文脈",
    "RDE評価",
    "注意点",
    "保存済み Sayane 文脈",
    "提案される変更",
)
_EXPORT_NOISE_EXACT: frozenset[str] = frozenset({
    "debug_only",
    "transient_session",
    "ui_noise",
})


def _is_noise_value(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped.lower() in _EXPORT_NOISE_EXACT:
        return True
    return any(pattern.lower() in stripped.lower() for pattern in _EXPORT_NOISE_SUBSTRINGS)


def _filter_noise_from_list(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        if isinstance(item, str):
            if _is_noise_value(item):
                continue
            key = item.strip().lower()
            if key in seen:
                continue
            seen.add(key)
        result.append(item)
    return result


def _clean_export_data(data: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, list):
            filtered = _filter_noise_from_list(value)
            if filtered:
                cleaned[key] = filtered
        elif isinstance(value, dict):
            nested = _clean_export_data(value)
            if nested:
                cleaned[key] = nested
        elif isinstance(value, str):
            if not _is_noise_value(value):
                cleaned[key] = value
        elif value is not None:
            cleaned[key] = value
    return cleaned


def _pick_profile_sections(profile: SayaneProfile, scopes: list[str]) -> dict[str, Any]:
    keys: set[str] = set()
    for scope in scopes:
        sections = SCOPE_SECTIONS.get(scope.strip().lower())
        if sections:
            keys.update(sections)
    profile_dict = profile.model_dump(mode="json")
    raw = {key: value for key, value in profile_dict.items() if key in keys and value is not None}
    return _clean_export_data(raw)


def export_yaml(profile: SayaneProfile, scopes: list[str]) -> str:
    """Export selected scopes as YAML."""
    import yaml

    data = _pick_profile_sections(profile, scopes)
    return yaml.safe_dump(data, allow_unicode=True, sort_keys=False)


def export_markdown(profile: SayaneProfile, scopes: list[str], target: str = "generic") -> str:
    """Export selected scopes as human-readable Markdown."""
    if target == "chatgpt":
        return _export_markdown_compact(profile, scopes, "ChatGPT")
    if target in ("claude", "anthropic"):
        return _export_markdown_compact(profile, scopes, "Claude")
    if target in ("gemini", "google"):
        return _export_markdown_compact(profile, scopes, "Gemini")
    if target == "deepseek":
        return _export_markdown_compact(profile, scopes, "DeepSeek")
    return _export_markdown_generic(profile, scopes, target)


def _append_identity(lines: list[str], ident: dict[str, Any], *, legacy_label: bool) -> None:
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


def _append_interaction(lines: list[str], data: dict[str, Any], heading: str) -> None:
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


def _append_values_and_policy(lines: list[str], data: dict[str, Any]) -> None:
    values = data.get("values")
    if isinstance(values, dict) and values.get("core"):
        lines.append("## Values")
        lines.append("")
        for value in values["core"]:
            lines.append(f"- {value}")
        lines.append("")
    policy = data.get("policy")
    if isinstance(policy, dict):
        response = policy.get("response")
        if isinstance(response, dict):
            prefer = response.get("prefer", [])
            avoid = response.get("avoid", [])
            if prefer or avoid:
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


def _append_knowledge_projects_terms(lines: list[str], data: dict[str, Any]) -> None:
    knowledge = data.get("knowledge")
    if isinstance(knowledge, dict) and knowledge.get("concepts"):
        lines.append("## Key Concepts")
        lines.append("")
        for concept in knowledge["concepts"]:
            lines.append(f"- {concept}")
        lines.append("")
    projects = data.get("major_projects", [])
    if projects:
        lines.append("## Projects")
        lines.append("")
        for project in projects:
            if isinstance(project, dict):
                name = project.get("name", "")
                summary = project.get("summary", "")
                lines.append(f"- **{name}**: {summary}" if summary else f"- {name}")
        lines.append("")
    terms = data.get("important_terms", [])
    if terms:
        lines.append("## Important Terms")
        lines.append("")
        for term in terms:
            lines.append(f"- {term}")
        lines.append("")


def _export_markdown_generic(profile: SayaneProfile, scopes: list[str], target: str) -> str:
    data = _pick_profile_sections(profile, scopes)
    lines: list[str] = ["# Sayane Context Bundle", "", f"Target: {target}", f"Scopes: {', '.join(scopes)}", ""]
    ident = data.get("identity")
    if isinstance(ident, dict):
        _append_identity(lines, ident, legacy_label=False)
    _append_interaction(lines, data, "## Interaction Style")
    _append_values_and_policy(lines, data)
    _append_knowledge_projects_terms(lines, data)
    return "\n".join(lines)


def _export_markdown_compact(profile: SayaneProfile, scopes: list[str], target_name: str) -> str:
    import datetime

    data = _pick_profile_sections(profile, scopes)
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
        _append_identity(lines, ident, legacy_label=True)
    _append_interaction(lines, data, "## Interaction Preferences")
    _append_values_and_policy(lines, data)
    _append_knowledge_projects_terms(lines, data)
    lines.append("## Export Policy Notes")
    lines.append("")
    lines.append("- Some private or sensitive fields may be omitted.")
    lines.append("- `promptExport: never` fields are not included.")
    lines.append("")
    return "\n".join(lines)


def export_prompt(profile: SayaneProfile, scopes: list[str], target: str = "generic") -> str:
    """Export as a compact prompt without promptExport-never contact fields."""
    data = _pick_profile_sections(profile, scopes)
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
    policy = data.get("policy")
    if isinstance(policy, dict):
        response = policy.get("response")
        if isinstance(response, dict):
            prefer = response.get("prefer", [])
            avoid = response.get("avoid", [])
            if prefer:
                lines.append("")
                lines.append("Preferred responses:")
                for item in prefer:
                    lines.append(f"- {item}")
            if avoid:
                lines.append("")
                lines.append("Avoid:")
                for item in avoid:
                    lines.append(f"- {item}")
    _append_knowledge_projects_terms(lines, data)
    return "\n".join(lines)
