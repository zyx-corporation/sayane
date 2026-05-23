"""Heuristic RDE classification (Level 1 — no LLM)."""

from omomuki.core.candidate import CandidateProposal, RDEClass

_CRITICAL_MARKERS = (
    "api key",
    "password",
    "secret",
    "private key",
    "identity.name",
    "values.core",
    "policy.response",
)
_IDENTITY_MARKERS = ("i am ", "my name is", "identity", "人格", "私は")
_SUSPICIOUS_MARKERS = (
    "you must",
    "always ",
    "never ",
    "personality is",
    "必ず",
    "絶対に",
)
_UNCERTAINTY_MARKERS = (
    "maybe",
    "perhaps",
    "might",
    "possibly",
    "推測",
    "不明",
    "uncertain",
)


def classify_rde(content: str, proposal: CandidateProposal) -> tuple[RDEClass, list[str]]:
    """Return RDE class and explanatory notes."""
    notes: list[str] = []
    lower = content.lower()

    if any(m in lower for m in _CRITICAL_MARKERS):
        notes.append("Content references critical profile fields or secrets.")
        if proposal.section.split(".")[0] in ("identity", "values", "policy", "voice"):
            return "Critical Distortion", notes
        return "Suspicious Drift", notes

    if any(m in lower for m in _IDENTITY_MARKERS) and proposal.section.startswith("identity"):
        notes.append("Identity-related change detected.")
        return "Critical Distortion", notes

    if len(content.strip()) < 20:
        notes.append("Capture too short for reliable merge judgment.")
        return "Unresolved Gap", notes

    if any(m in lower for m in _SUSPICIOUS_MARKERS):
        notes.append("Imperative or overconfident phrasing detected.")
        return "Suspicious Drift", notes

    if not proposal.add:
        notes.append("No concrete proposal items extracted.")
        return "Unresolved Gap", notes

    if proposal.section == "knowledge.concepts":
        notes.append("Non-critical knowledge extension from capture.")
        return "Inferred Extension", notes

    notes.append("Section change requires manual review.")
    return "Authorized Transformation", notes
