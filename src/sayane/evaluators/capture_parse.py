"""YAML / persona capture parsing and parse-failure handling."""

from __future__ import annotations

import re
from typing import Any

import yaml

from sayane.core.candidate import CandidateProposal, CaptureMetadata
from sayane.core.models import SayaneProfile
from sayane.evaluators.list_diff import (
    important_terms_display_summary,
    important_terms_profile_diff,
)

SECTION_REVIEW_REQUIRED = "review_required"
OPERATION_PARSE_FAILED = "parse_failed"
OPERATION_NO_EFFECTIVE = "parse_failed_or_no_effective_update"

# Inline key after quoted string on the same line — common copy/paste breakage.
_BROKEN_INLINE_KEY_RE = re.compile(
    r'["\'][^"\']*["\'][ \t]{2,}[a-z][a-z0-9_]*:\s*',
    re.IGNORECASE,
)

_YAML_LIKE_RE = re.compile(
    r"^(persona|person|organization|development_preferences|writing_preferences|"
    r"communication_mode|major_projects|projects|values|identity|important_terms)\s*:",
    re.IGNORECASE | re.MULTILINE,
)

_PERSONA_ROOT_KEYS = frozenset(
    {
        "persona",
        "person",
        "organization",
        "development_preferences",
        "writing_preferences",
        "communication_mode",
        "identity",
        "values",
        "projects",
        "major_projects",
    },
)


def looks_like_yaml_capture(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return False
    if stripped.startswith("{") or stripped.startswith("["):
        return True
    if _BROKEN_INLINE_KEY_RE.search(content):
        return True
    if re.search(r"(?m)^persona\s*:", content):
        return True
    return bool(_YAML_LIKE_RE.search(stripped))


def detect_yaml_syntax_error(content: str) -> str | None:
    if _BROKEN_INLINE_KEY_RE.search(content):
        m = _BROKEN_INLINE_KEY_RE.search(content)
        if m:
            tail = content[m.start() : m.start() + 80]
            key_match = re.search(r"([a-z][a-z0-9_]*):\s*$", tail, re.IGNORECASE)
            if key_match:
                return f"YAML parse failed near {key_match.group(1)}"
        return "YAML parse failed: inline key after quoted value"
    try:
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as err:
        msg = str(err).split("\n")[0]
        return f"YAML parse failed: {msg[:120]}"


def try_parse_yaml(content: str) -> tuple[Any | None, str | None]:
    err = detect_yaml_syntax_error(content)
    if err:
        return None, err
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as err:
        return None, f"YAML parse failed: {str(err).splitlines()[0][:120]}"
    if parsed is None:
        return None, "YAML parse failed: empty document"
    return parsed, None


def top_level_yaml_keys(parsed: dict[str, Any]) -> set[str]:
    return {str(k).lower() for k in parsed.keys()}


def persona_document_keys(parsed: dict[str, Any]) -> set[str]:
    keys = top_level_yaml_keys(parsed)
    return keys & _PERSONA_ROOT_KEYS


def build_parse_failed_proposal(parse_error: str) -> CandidateProposal:
    return CandidateProposal(
        section=SECTION_REVIEW_REQUIRED,
        operation=OPERATION_PARSE_FAILED,
        add=[],
        items=[],
        already_present=[],
        summary=parse_error,
        parse_error=parse_error,
    )


def build_no_effective_proposal(reason: str) -> CandidateProposal:
    return CandidateProposal(
        section=SECTION_REVIEW_REQUIRED,
        operation=OPERATION_NO_EFFECTIVE,
        add=[],
        items=[],
        already_present=[],
        summary=reason,
    )


def _normalize_scalar(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(_normalize_scalar(v) for v in value if v is not None)
    return str(value).strip()


def _walk_profile_values(profile: SayaneProfile) -> dict[str, list[str]]:
    """Flatten profile scalars for already_present matching."""
    index: dict[str, list[str]] = {}

    def add(path: str, raw: str) -> None:
        key = raw.strip().casefold()
        if key:
            index.setdefault(key, []).append(path)

    add("identity.name", profile.identity.name)
    if profile.identity.preferred_name:
        add("identity.preferred_name", profile.identity.preferred_name)
    for role in profile.identity.roles:
        add("identity.roles[]", role)
    if profile.organization and profile.organization.name:
        add("organization.name", profile.organization.name)
    mode = profile.communication_mode
    if mode:
        for field, val in (
            ("communication_mode.assistant_name_for_chatgpt", mode.assistant_name_for_chatgpt),
            ("communication_mode.preferred_address", mode.preferred_address),
            ("communication_mode.intimate_address", mode.intimate_address),
        ):
            if val:
                add(field, val)
        for style in mode.collaboration_style:
            add("communication_mode.collaboration_style[]", style)
    for term in profile.important_terms:
        add("important_terms[]", term)
    for concept in profile.knowledge.concepts if profile.knowledge else []:
        add("core_concepts[].name", concept)
    for project in profile.major_projects:
        add("major_projects[].name", project.name)
        if project.summary:
            add(f"major_projects[].name:{project.name.casefold()}", project.summary)
    return index


def _collect_yaml_scalars(
    node: Any,
    path: str,
    out: list[tuple[str, str, str]],
) -> None:
    if isinstance(node, dict):
        for key, val in node.items():
            key_str = str(key)
            child = f"{path}.{key_str}" if path else key_str
            _collect_yaml_scalars(val, child, out)
        return
    if isinstance(node, list):
        for i, item in enumerate(node):
            _collect_yaml_scalars(item, f"{path}[{i}]", out)
        return
    text = _normalize_scalar(node)
    if text and path:
        section = path.split(".")[0].split("[")[0]
        out.append((section, path, text))


def classify_persona_yaml(
    parsed: dict[str, Any],
    profile: SayaneProfile | None,
) -> CandidateProposal:
    keys = persona_document_keys(parsed)
    if "persona" in keys and len(keys) == 1:
        root = parsed.get("persona") or parsed.get("Persona")
        if isinstance(root, dict):
            parsed = {"persona": root, **{k: v for k, v in parsed.items() if k != "persona"}}
            keys = persona_document_keys(parsed)

    scalars: list[tuple[str, str, str]] = []
    _collect_yaml_scalars(parsed, "", scalars)

    profile_index = _walk_profile_values(profile) if profile else {}
    already_present: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    sections_seen: set[str] = set()

    for section, path, text in scalars:
        if section in _PERSONA_ROOT_KEYS or section in {
            "preferred_name",
            "formal_name",
            "email",
            "role",
        }:
            sections_seen.add(section if section in _PERSONA_ROOT_KEYS else "persona")
        key = text.casefold()
        paths = profile_index.get(key, [])
        if paths:
            already_present.append({"path": paths[0], "name": text, "yaml_path": path})
        else:
            items.append({"section": section or "persona", "name": text, "yaml_path": path})

    if len(keys) > 1 or len(sections_seen) > 1:
        section = "mixed_sections"
        operation = "no_op_or_duplicate" if not items else "add_or_update"
    elif not items and already_present:
        section = SECTION_REVIEW_REQUIRED
        operation = OPERATION_NO_EFFECTIVE
    elif not items and not already_present:
        section = SECTION_REVIEW_REQUIRED
        operation = OPERATION_NO_EFFECTIVE
    else:
        section = "mixed_sections" if len({i.get("section") for i in items}) > 1 else (
            items[0].get("section", "persona") if items else SECTION_REVIEW_REQUIRED
        )
        operation = "add_or_update" if items else OPERATION_NO_EFFECTIVE

    summary = (
        f"Persona YAML: {len(items)} new field(s), {len(already_present)} already in profile"
    )
    return CandidateProposal(
        section=section,
        operation=operation,
        add=[],
        items=items,
        already_present=already_present,
        summary=summary,
    )


def classify_important_terms_yaml(
    parsed: dict[str, Any],
    profile: SayaneProfile | None,
) -> CandidateProposal:
    terms_raw = parsed.get("important_terms")
    if not isinstance(terms_raw, list):
        return build_parse_failed_proposal("important_terms must be a YAML list")
    captured: list[str] = []
    for entry in terms_raw:
        text = _normalize_scalar(entry)
        if text:
            captured.append(text)
    existing = list(profile.important_terms) if profile else []
    ld = important_terms_profile_diff(existing, captured)
    items = [
        {
            "section": "important_terms",
            "name": name,
            "yaml_path": "important_terms[]",
        }
        for name in ld.added
    ]
    already_present = [
        {
            "path": "important_terms[]",
            "name": name,
            "yaml_path": "important_terms[]",
        }
        for name in ld.unchanged
    ]
    if not items and already_present:
        operation = "no_op_or_duplicate"
    elif items:
        operation = "list_add"
    else:
        operation = OPERATION_NO_EFFECTIVE
    summary = important_terms_display_summary(
        CandidateProposal(
            section="important_terms",
            operation=operation,
            items=items,
            already_present=already_present,
        ),
    )
    return CandidateProposal(
        section="important_terms",
        operation=operation,
        add=[],
        items=items,
        already_present=already_present,
        summary=summary,
    )


def build_proposal_for_yaml_content(
    content: str,
    profile: SayaneProfile | None,
    capture_meta: CaptureMetadata | None,
) -> CandidateProposal | None:
    if not looks_like_yaml_capture(content):
        return None

    parsed, err = try_parse_yaml(content)
    if err:
        return build_parse_failed_proposal(err)

    if not isinstance(parsed, dict):
        return build_parse_failed_proposal("YAML parse failed: root must be a mapping")

    keys = top_level_yaml_keys(parsed)
    if keys == {"important_terms"} or (
        len(keys) == 1 and "important_terms" in keys
    ):
        return classify_important_terms_yaml(parsed, profile)
    if "persona" in keys or "person" in keys:
        return classify_persona_yaml(parsed, profile)

    return None
