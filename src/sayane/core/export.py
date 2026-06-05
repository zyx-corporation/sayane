"""Context Portability export: yaml / markdown / prompt with scope and policy."""

from __future__ import annotations

from typing import Any

from sayane.core.models import SayaneProfile

# --- Scope → top-level profile section keys ---

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

_PROMPT_NEVER_SECTIONS: frozenset[str] = frozenset({
    "identity.contact",
})

# --- Export noise filtering (#155) ---
# These are structural noise patterns, not i18n-dependent text.
# They match fragments that leak from capture/review UI into profile data.

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
    """Check if a string value is export noise."""
    stripped = value.strip()
    if not stripped:
        return True
    if stripped.lower() in _EXPORT_NOISE_EXACT:
        return True
    for pattern in _EXPORT_NOISE_SUBSTRINGS:
        if pattern.lower() in stripped.lower():
            return True
    return False


def _filter_noise_from_list(items: list[Any]) -> list[Any]:
    """Remove noise entries and deduplicate a list."""
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
        elif isinstance(item, dict):
            result.append(item)
        else:
            result.append(item)
    return result


def _clean_export_data(data: dict[str, Any]) -> dict[str, Any]:
    """Apply noise filtering to profile data before export. Recurses into nested dicts."""
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
    """Return a nested dict of profile sections covered by the requested scopes."""
    keys: set[str] = set()
    for scope in scopes:
        sections = SCOPE_SECTIONS.get(scope.strip().lower())
        if sections:
            keys.update(sections)

    profile_dict = profile.model_dump(mode="json")
    raw = {k: v for k, v in profile_dict.items() if k in keys and v is not None}
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


def _export_markdown_generic(profile: SayaneProfile, scopes: list[str], target: str) -> str:
    data = _pick_profile_sections(profile, scopes)
    lines: list[str] = []
    lines.append(f"# Sayane Context Bundle")
    lines.append(f"")
    lines.append(f"Target: {target}")
    lines.append(f"Scopes: {', '.join(scopes)}")
    lines.append(f"")

    ident = data.get("identity")
    if isinstance(ident, dict):
        lines.append("## Identity")
        lines.append("")
        if ident.get("name"):
            lines.append(f"- Name: {ident['name']}")
        if ident.get("preferred_name"):
            lines.append(f"- Preferred name: {ident['preferred_name']}")
        roles = ident.get("roles", [])
        if roles:
            lines.append(f"- Roles: {', '.join(roles)}")
        lines.append("")

    voice = data.get("voice")
    cm = data.get("communication_mode")
    if isinstance(voice, dict) or isinstance(cm, dict):
        lines.append("## Interaction Style")
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
                lines.append(f"- Address style: {cm['preferred_address']}")
            cs = cm.get("collaboration_style", [])
            if cs:
                lines.append(f"- Collaboration: {', '.join(cs)}")
        lines.append("")

    values = data.get("values")
    if isinstance(values, dict):
        core = values.get("core", [])
        if core:
            lines.append("## Values")
            lines.append("")
            for v in core:
                lines.append(f"- {v}")
            lines.append("")

    policy = data.get("policy")
    if isinstance(policy, dict):
        resp = policy.get("response")
        if isinstance(resp, dict):
            prefer = resp.get("prefer", [])
            avoid = resp.get("avoid", [])
            if prefer or avoid:
                lines.append("## Response Policy")
                lines.append("")
                if prefer:
                    lines.append("Prefer:")
                    for p in prefer:
                        lines.append(f"- {p}")
                if avoid:
                    lines.append("Avoid:")
                    for a in avoid:
                        lines.append(f"- {a}")
                lines.append("")

    knowledge = data.get("knowledge")
    if isinstance(knowledge, dict):
        concepts = knowledge.get("concepts", [])
        if concepts:
            lines.append("## Key Concepts")
            lines.append("")
            for c in concepts:
                lines.append(f"- {c}")
            lines.append("")

    projects = data.get("major_projects", [])
    if projects:
        lines.append("## Projects")
        lines.append("")
        for p in projects:
            if isinstance(p, dict):
                lines.append(f"- **{p.get('name', '')}**: {p.get('summary', '')}" if p.get("summary") else f"- {p.get('name', '')}")
        lines.append("")

    terms = data.get("important_terms", [])
    if terms:
        lines.append("## Important Terms")
        lines.append("")
        for t in terms:
            lines.append(f"- {t}")
        lines.append("")

    return "\n".join(lines)


def export_prompt(profile: SayaneProfile, scopes: list[str], target: str = "generic") -> str:
    """Export as a compact prompt. Fields with promptExport 'never' (email etc.) are excluded from scopes by default."""
    data = _pick_profile_sections(profile, scopes)
    lines: list[str] = []
    lines.append("[Context]")
    lines.append("")

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
            cs = cm.get("collaboration_style", [])
            if cs:
                lines.append(f"Collaboration: {', '.join(cs)}")

    values = data.get("values")
    if isinstance(values, dict):
        core = values.get("core", [])
        if core:
            lines.append("")
            lines.append("Values:")
            for v in core:
                lines.append(f"- {v}")

    policy = data.get("policy")
    if isinstance(policy, dict):
        resp = policy.get("response")
        if isinstance(resp, dict):
            prefer = resp.get("prefer", [])
            avoid = resp.get("avoid", [])
            if prefer:
                lines.append("")
                lines.append("Preferred responses:")
                for p in prefer:
                    lines.append(f"- {p}")
            if avoid:
                lines.append("")
                lines.append("Avoid:")
                for a in avoid:
                    lines.append(f"- {a}")

    knowledge = data.get("knowledge")
    if isinstance(knowledge, dict):
        concepts = knowledge.get("concepts", [])
        if concepts:
            lines.append("")
            lines.append("Key concepts:")
            for c in concepts:
                lines.append(f"- {c}")

    projects = data.get("major_projects", [])
    if projects:
        lines.append("")
        lines.append("Relevant projects:")
        for p in projects:
            if isinstance(p, dict):
                lines.append(f"- {p.get('name', '')}")

    terms = data.get("important_terms", [])
    if terms:
        lines.append("")
        lines.append("Important terms:")
        for t in terms:
            lines.append(f"- {t}")

    return "\n".join(lines)


def _export_markdown_compact(profile: SayaneProfile, scopes: list[str], target_name: str) -> str:
    """Refined compact format with metadata, quote/interpretation, principles, execution_context."""
    import datetime
    data = _pick_profile_sections(profile, scopes)
    lines: list[str] = []
    now = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%dT%H:%M:%SZ")

    # Header
    lines.append(f"# Sayane External Profile for {target_name}")
    lines.append("")

    # Metadata
    lines.append("## Metadata")
    lines.append("")
    lines.append(f"- Source: Sayane external profile")
    lines.append(f"- LLM memory: false")
    lines.append(f"- Generated: {now}")
    lines.append(f"- Target: {target_name}")
    lines.append(f"- Format: markdown")
    lines.append(f"- Scopes: {', '.join(scopes)}")
    lines.append("")

    # Usage note
    lines.append("## How to Use This Context")
    lines.append("")
    lines.append(
        "This profile is external context supplied by Sayane. It is not "
        f"{target_name} memory. "
        "Sayane is the external context portability system that generated "
        "this profile. It is not the receiving assistant's name, identity, or memory. "
        "This profile does not rename or redefine the receiving assistant. "
        "Use it to guide responses within this session, "
        "while respecting explicit uncertainty and avoiding unsupported assumptions."
    )
    lines.append("")

    # Identity
    ident = data.get("identity")
    if isinstance(ident, dict):
        lines.append("## Identity")
        lines.append("")
        if ident.get("name"):
            lines.append(f"- Name: {ident['name']}")
        if ident.get("preferred_name"):
            lines.append(f"- Preferred name: {ident['preferred_name']}")
        roles = ident.get("roles", [])
        if roles:
            lines.append(f"- Roles: {', '.join(roles)}")
        lines.append("")

    # Interaction
    voice = data.get("voice")
    cm = data.get("communication_mode")
    if isinstance(voice, dict) or isinstance(cm, dict):
        lines.append("## Interaction Preferences")
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
            cs = cm.get("collaboration_style", [])
            if cs:
                lines.append(f"- Collaboration style: {', '.join(cs)}")
        lines.append("")

    # Philosophical Stance (from values)
    values = data.get("values")
    has_axioms = False
    if isinstance(values, dict):
        core = values.get("core", [])
        if core:
            lines.append("## Philosophical Stance")
            lines.append("")
            for i, axiom in enumerate(core):
                lines.append(f"### Axiom {i + 1}")
                lines.append("")
                lines.append("Quote:")
                lines.append("")
                lines.append(f"> {axiom}")
                lines.append("")
                lines.append("Interpretation: not provided")
                lines.append("")
                has_axioms = True

    # Principles (from knowledge concepts)
    knowledge = data.get("knowledge")
    if isinstance(knowledge, dict):
        concepts = knowledge.get("concepts", [])
        if concepts:
            lines.append("## Principles")
            lines.append("")
            for c in concepts:
                lines.append(f"- {c}")
            lines.append("")

    # Policy
    policy = data.get("policy")
    if isinstance(policy, dict):
        resp = policy.get("response")
        if isinstance(resp, dict):
            prefer = resp.get("prefer", [])
            avoid = resp.get("avoid", [])
            if prefer or avoid:
                lines.append("## Response Policy")
                lines.append("")
                if prefer:
                    lines.append("Prefer:")
                    for p in prefer:
                        lines.append(f"- {p}")
                if avoid:
                    lines.append("")
                    lines.append("Avoid:")
                    for a in avoid:
                        lines.append(f"- {a}")
                lines.append("")

    # Technical / Concepts
    if isinstance(knowledge, dict) and "philosophy" not in scopes:
        # Only show as Concepts if not already shown as Principles
        concepts = knowledge.get("concepts", [])
        if concepts and "principles" not in scopes:
            lines.append("## Technical Preferences")
            lines.append("")
            for c in concepts:
                lines.append(f"- {c}")
            lines.append("")

    # Execution Context
    projects = data.get("major_projects", [])
    exec_cm = data.get("communication_mode")
    has_exec = bool(projects) or isinstance(exec_cm, dict)
    if has_exec:
        lines.append("## Execution Context")
        lines.append("")
        if projects:
            lines.append("### Projects")
            lines.append("")
            for p in projects:
                if isinstance(p, dict):
                    name = p.get("name", "")
                    summary = p.get("summary", "")
                    lines.append(f"- **{name}**: {summary}" if summary else f"- {name}")
            lines.append("")

    # Important Terms
    terms = data.get("important_terms", [])
    if terms:
        lines.append("## Important Terms")
        lines.append("")
        for t in terms:
            lines.append(f"- {t}")
        lines.append("")

    # Export Policy Notes
    lines.append("## Export Policy Notes")
    lines.append("")
    lines.append("- Some private or sensitive fields may be omitted.")
    lines.append("- `promptExport: never` fields are not included.")
    lines.append("")

    return "\n".join(lines)
