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

_BROKEN_INLINE_KEY_RE = re.compile(
    r'["\'][^"\']*["\'][ \t]{2,}[a-z][a-z0-9_]*:\s*',
    re.IGNORECASE,
)
_YAML_LIKE_RE = re.compile(
    r"^(persona|person|organization|development_preferences|writing_preferences|"
    r"communication_mode|major_projects|projects|values|identity|important_terms)\s*:",
    re.IGNORECASE | re.MULTILINE,
)
_MARKDOWN_HEADING_RE = re.compile(r"(?m)^#+\s+")
_MARKDOWN_BULLET_RE = re.compile(r"(?m)^\s*[-*•]\s+")
_IMPORTANT_TERMS_FRAGMENT_RE = re.compile(r"(?m)^\s*important_terms\s*:\s*$", re.IGNORECASE)
_LIST_ITEM_RE = re.compile(r"^\s*-\s*(.+?)\s*$")

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
    }
)


def looks_like_yaml_capture(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return False
    if _extract_important_terms_fragment(content):
        return True
    if _MARKDOWN_HEADING_RE.search(content) and _MARKDOWN_BULLET_RE.search(content):
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
    return str(value).strip().strip('"\'')


def _extract_important_terms_fragment(content: str) -> list[str]:
    lines = content.splitlines()
    terms: list[str] = []
    in_section = False
    section_indent = 0
    for line in lines:
        if not in_section:
            match = _IMPORTANT_TERMS_FRAGMENT_RE.match(line)
            if match:
                in_section = True
                section_indent = len(line) - len(line.lstrip())
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= section_indent and not _LIST_ITEM_RE.match(line):
            break
        item = _LIST_ITEM_RE.match(line)
        if item:
            text = _normalize_scalar(item.group(1))
            if text:
                terms.append(text)
    return terms


def _walk_profile_values(profile: SayaneProfile) -> dict[str, list[str]]:
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


def _collect_yaml_scalars(node: Any, path: str, out: list[tuple[str, str, str]]) -> None:
    if isinstance(node, dict):
        for key, val in node.items():
            child = f"{path}.{key}" if path else str(key)
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


def classify_persona_yaml(parsed: dict[str, Any], profile: SayaneProfile | None) -> CandidateProposal:
    keys = persona_document_keys(parsed)
    scalars: list[tuple[str, str, str]] = []
    _collect_yaml_scalars(parsed, "", scalars)
    profile_index = _walk_profile_values(profile) if profile else {}
    already_present: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    sections_seen: set[str] = set()
    for section, path, text in scalars:
        if section in _PERSONA_ROOT_KEYS or section in {"preferred_name", "formal_name", "email", "role"}:
            sections_seen.add(section if section in _PERSONA_ROOT_KEYS else "persona")
        paths = profile_index.get(text.casefold(), [])
        if paths:
            already_present.append({"path": paths[0], "name": text, "yaml_path": path})
        else:
            items.append({"section": section or "persona", "name": text, "yaml_path": path})
    if len(keys) > 1 or len(sections_seen) > 1:
        section = "mixed_sections"
        operation = "no_op_or_duplicate" if not items else "add_or_update"
    elif not items:
        section = SECTION_REVIEW_REQUIRED
        operation = OPERATION_NO_EFFECTIVE
    else:
        item_sections = {item.get("section") for item in items}
        section = "mixed_sections" if len(item_sections) > 1 else items[0].get("section", "persona")
        operation = "add_or_update"
    return CandidateProposal(
        section=section,
        operation=operation,
        add=[],
        items=items,
        already_present=already_present,
        summary=f"Persona YAML: {len(items)} new field(s), {len(already_present)} already in profile",
    )


def classify_important_terms_yaml(parsed: dict[str, Any], profile: SayaneProfile | None) -> CandidateProposal:
    terms_raw = parsed.get("important_terms")
    if not isinstance(terms_raw, list):
        return build_parse_failed_proposal("important_terms must be a YAML list")
    captured = [_normalize_scalar(entry) for entry in terms_raw if _normalize_scalar(entry)]
    existing = list(profile.important_terms) if profile else []
    ld = important_terms_profile_diff(existing, captured)
    items = [{"section": "important_terms", "name": name, "yaml_path": "important_terms[]"} for name in ld.added]
    already_present = [{"path": "important_terms[]", "name": name, "yaml_path": "important_terms[]"} for name in ld.unchanged]
    removed = [{"path": "important_terms[]", "name": name, "yaml_path": "important_terms[]"} for name in ld.removed]
    if not items and already_present and not removed:
        operation = "no_op_or_duplicate"
    elif not items and removed:
        operation = "list_remove"
    elif items and removed:
        operation = "list_update"
    elif items:
        operation = "list_add"
    else:
        operation = OPERATION_NO_EFFECTIVE
    proposal = CandidateProposal(
        section="important_terms",
        operation=operation,
        add=[],
        items=items,
        remove=removed,
        already_present=already_present,
    )
    proposal.summary = important_terms_display_summary(proposal)
    return proposal


def build_proposal_for_yaml_content(content: str, profile: SayaneProfile | None, capture_meta: CaptureMetadata | None) -> CandidateProposal | None:
    fragment_terms = _extract_important_terms_fragment(content)
    if fragment_terms:
        return classify_important_terms_yaml({"important_terms": fragment_terms}, profile)
    if not looks_like_yaml_capture(content):
        return None
    parsed, err = try_parse_yaml(content)
    if err:
        return build_parse_failed_proposal(err)
    if not isinstance(parsed, dict):
        return build_parse_failed_proposal("YAML parse failed: root must be a mapping")
    keys = top_level_yaml_keys(parsed)
    if "important_terms" in keys and len(keys) == 1:
        return classify_important_terms_yaml(parsed, profile)
    if "persona" in keys or "person" in keys:
        return classify_persona_yaml(parsed, profile)
    return None
