"""Profile section helpers for proposals and merge policy."""

from __future__ import annotations

from sayane.evaluators.heuristic_match import (
    contains_dot_path,
    has_core_values_phrase,
    has_yaml_key,
)

CRITICAL_ROOTS = frozenset({"identity", "values", "policy", "voice"})
BLOCKED_SECTIONS = frozenset({"identity.name", "identity.preferred_name"})
FORCE_ALLOWED_SECTIONS = frozenset(
    {
        "values.core",
        "voice.tone",
        "policy.response.avoid",
        "policy.response.prefer",
        "identity.roles",
        "knowledge.concepts",
        "important_terms",
        "major_projects",
        "communication_mode",
    },
)
PROPOSAL_SECTIONS = FORCE_ALLOWED_SECTIONS


def normalize_proposal_section(section: str) -> str:
    """Validate an explicit capture/merge target section."""
    name = section.strip()
    if name not in PROPOSAL_SECTIONS:
        allowed = ", ".join(sorted(PROPOSAL_SECTIONS))
        raise ValueError(
            f"Unknown proposal section '{section}'. Allowed: {allowed}",
        )
    return name


_PERSONA_ROOT_KEYS = (
    "person:",
    "organization:",
    "relationships:",
    "formation:",
    "philosophy:",
    "theory:",
    "projects:",
    "interaction_style:",
    "health:",
)


def looks_like_structured_persona(content: str) -> bool:
    """Multi-root persona documents are not a single Sayane section."""
    hits = 0
    for line in content.splitlines():
        stripped = line.strip()
        if any(stripped.startswith(key) for key in _PERSONA_ROOT_KEYS):
            hits += 1
        if hits >= 2:
            return True
    return False


def infer_proposal_section(
    content: str,
    *,
    structured_items: list[dict[str, str]] | None = None,
    communication_items: list[dict[str, str]] | None = None,
) -> str:
    """Guess target section from capture text markers."""
    if structured_items:
        return "major_projects"
    if communication_items:
        return "communication_mode"
    if looks_like_structured_persona(content):
        return "knowledge.concepts"

    if contains_dot_path(content, "policy.response.avoid") or has_yaml_key(
        content,
        "avoid",
    ):
        return "policy.response.avoid"
    if contains_dot_path(content, "policy.response.prefer") or has_yaml_key(
        content,
        "prefer",
    ):
        return "policy.response.prefer"
    if contains_dot_path(
        content,
        "values.core",
    ) or has_core_values_phrase(content):
        return "values.core"
    if contains_dot_path(content, "voice.tone") or has_yaml_key(content, "tone"):
        return "voice.tone"
    if contains_dot_path(
        content,
        "identity.roles",
    ) or has_yaml_key(content, "roles"):
        return "identity.roles"
    return "knowledge.concepts"


def is_critical_section(section: str) -> bool:
    root = section.split(".")[0]
    return root in CRITICAL_ROOTS


def can_merge_section(section: str, *, force_critical: bool) -> bool:
    if section in BLOCKED_SECTIONS:
        return False
    if section == "knowledge.concepts":
        return True
    if force_critical and section in FORCE_ALLOWED_SECTIONS:
        return True
    if not is_critical_section(section):
        return True
    return False
