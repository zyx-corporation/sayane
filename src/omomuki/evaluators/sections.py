"""Profile section helpers for proposals and merge policy."""

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
    },
)


def infer_proposal_section(content: str) -> str:
    """Guess target section from capture text markers."""
    lower = content.lower()
    if "policy.response.avoid" in lower or "avoid:" in lower:
        return "policy.response.avoid"
    if "policy.response.prefer" in lower or "prefer:" in lower:
        return "policy.response.prefer"
    if "values.core" in lower or "core value" in lower:
        return "values.core"
    if "voice.tone" in lower or "tone:" in lower:
        return "voice.tone"
    if "identity.roles" in lower or "roles:" in lower:
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
