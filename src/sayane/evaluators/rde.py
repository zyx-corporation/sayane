"""Heuristic RDE classification (Level 1 — no LLM)."""

from sayane.core.candidate import CandidateProposal, RDEClass
from sayane.evaluators.heuristic_match import (
    contains_any_dot_path,
    contains_any_phrase,
    contains_phrase,
    contains_word,
    has_imperative_always,
    has_imperative_never,
)

_CRITICAL_PHRASES = (
    "api key",
    "private key",
)
_CRITICAL_WORDS = ("password",)
_CRITICAL_DOT_PATHS = (
    "identity.name",
    "values.core",
    "policy.response",
)
_SECRET_PHRASES = (
    "secret key",
    "client secret",
    "shared secret",
    "my secret",
)

_IDENTITY_PHRASES = (
    "i am ",
    "my name is",
)
_IDENTITY_WORDS_JA = ("人格", "私は")

_SUSPICIOUS_PHRASES = (
    "you must",
    "personality is",
)
_SUSPICIOUS_WORDS_JA = (
    "必ず",
    "絶対に",
)


def _references_critical_content(content: str) -> bool:
    if contains_any_phrase(content, _CRITICAL_PHRASES):
        return True
    if contains_any_dot_path(content, _CRITICAL_DOT_PATHS):
        return True
    if any(contains_word(content, w) for w in _CRITICAL_WORDS):
        return True
    if contains_any_phrase(content, _SECRET_PHRASES):
        return True
    return False


def _references_identity_change(content: str) -> bool:
    if any(marker in content for marker in _IDENTITY_WORDS_JA):
        return True
    return any(contains_phrase(content, p) for p in _IDENTITY_PHRASES)


def _has_suspicious_imperative(content: str) -> bool:
    if contains_any_phrase(content, _SUSPICIOUS_PHRASES):
        return True
    if has_imperative_always(content) or has_imperative_never(content):
        return True
    return any(marker in content for marker in _SUSPICIOUS_WORDS_JA)


def classify_rde(content: str, proposal: CandidateProposal) -> tuple[RDEClass, list[str]]:
    """Return RDE class and explanatory notes."""
    notes: list[str] = []

    if _references_critical_content(content):
        notes.append("Content references critical profile fields or secrets.")
        if proposal.section.split(".")[0] in ("identity", "values", "policy", "voice"):
            return "Critical Distortion", notes
        return "Suspicious Drift", notes

    if _references_identity_change(content) and proposal.section.startswith("identity"):
        notes.append("Identity-related change detected.")
        return "Critical Distortion", notes

    if len(content.strip()) < 20:
        notes.append("Capture too short for reliable merge judgment.")
        return "Unresolved Gap", notes

    if _has_suspicious_imperative(content):
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
