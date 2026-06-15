"""Persona YAML classification helpers."""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import CandidateProposal
from sayane.core.models import SayaneProfile
from sayane.evaluators.important_terms_fragment import normalize_scalar
from sayane.evaluators.yaml_detection import PERSONA_ROOT_KEYS, persona_document_keys

SECTION_REVIEW_REQUIRED = "review_required"
OPERATION_NO_EFFECTIVE = "parse_failed_or_no_effective_update"


def walk_profile_values(profile: SayaneProfile) -> dict[str, list[str]]:
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


def collect_yaml_scalars(node: Any, path: str, out: list[tuple[str, str, str]]) -> None:
    if isinstance(node, dict):
        for key, val in node.items():
            child = f"{path}.{key}" if path else str(key)
            collect_yaml_scalars(val, child, out)
        return
    if isinstance(node, list):
        for i, item in enumerate(node):
            collect_yaml_scalars(item, f"{path}[{i}]", out)
        return
    text = normalize_scalar(node)
    if text and path:
        section = path.split(".")[0].split("[")[0]
        out.append((section, path, text))


def classify_persona_yaml(parsed: dict[str, Any], profile: SayaneProfile | None) -> CandidateProposal:
    keys = persona_document_keys(parsed)
    scalars: list[tuple[str, str, str]] = []
    collect_yaml_scalars(parsed, "", scalars)
    profile_index = walk_profile_values(profile) if profile else {}
    already_present: list[dict[str, str]] = []
    items: list[dict[str, str]] = []
    sections_seen: set[str] = set()
    for section, path, text in scalars:
        if section in PERSONA_ROOT_KEYS or section in {"preferred_name", "formal_name", "email", "role"}:
            sections_seen.add(section if section in PERSONA_ROOT_KEYS else "persona")
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
