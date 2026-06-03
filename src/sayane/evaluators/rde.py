"""Heuristic RDE classification (Level 1 — no LLM)."""

from sayane.core.candidate import CandidateProposal, RDEClass
from sayane.core.evaluation_notes import EvaluationNote, heuristic_note
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


def classify_rde(
    content: str,
    proposal: CandidateProposal,
) -> tuple[RDEClass, list[EvaluationNote]]:
    """Return RDE class and structured explanatory notes."""
    notes: list[EvaluationNote] = []

    if _references_critical_content(content):
        notes.append(
            heuristic_note("content_references_critical_profile_fields"),
        )
        if proposal.section.split(".")[0] in (
            "identity",
            "values",
            "policy",
            "voice",
        ):
            return "Critical Distortion", notes
        return "Suspicious Drift", notes

    if (
        _references_identity_change(content)
        and proposal.section.startswith("identity")
    ):
        notes.append(heuristic_note("identity_related_change_detected"))
        return "Critical Distortion", notes

    if len(content.strip()) < 20:
        notes.append(heuristic_note("capture_too_short"))
        return "Unresolved Gap", notes

    if proposal.operation in ("parse_failed", "parse_failed_or_no_effective_update"):
        notes.append(heuristic_note("yaml_parse_failed"))
        return "Unresolved Gap", notes

    if proposal.section == "review_required":
        notes.append(heuristic_note("review_required_no_auto_merge"))
        return "Unresolved Gap", notes

    if proposal.section == "mixed_sections":
        notes.append(heuristic_note("multiple_profile_sections_mixed"))
        if proposal.already_present and not proposal.items:
            notes.append(
                heuristic_note("proposal_overlaps_existing_across_sections"),
            )
            return "Suspicious Drift", notes
        return "Unresolved Gap", notes

    if _has_suspicious_imperative(content):
        notes.append(heuristic_note("imperative_or_overconfident_phrasing"))
        return "Suspicious Drift", notes

    project_style_items = [item for item in proposal.items if "name" in item]
    if proposal.section == "knowledge.concepts" and project_style_items:
        notes.append(heuristic_note("project_items_in_concepts"))
        notes.append(heuristic_note("potential_redundancy_with_major_projects"))
        return "Suspicious Drift", notes

    if proposal.section == "major_projects":
        if proposal.operation == "no_op_or_duplicate":
            notes.append(
                heuristic_note("no_effective_profile_update_major_projects"),
            )
            return "Preserved", notes
        notes.append(heuristic_note("project_updates_inferred"))
        return "Inferred Extension", notes

    communication_items = [
        item for item in proposal.items
        if item.get("path", "").startswith("communication_mode.")
    ]
    if proposal.section == "communication_mode":
        if proposal.operation == "no_op_or_duplicate":
            notes.append(
                heuristic_note("no_effective_profile_update_communication_mode"),
            )
            return "Preserved", notes
        notes.append(heuristic_note("communication_mode_requires_manual_review"))
        return "Unresolved Gap", notes
    if proposal.section == "knowledge.concepts" and communication_items:
        notes.append(heuristic_note("communication_mode_values_in_concepts"))
        return "Unresolved Gap", notes

    if not proposal.add and not proposal.items:
        notes.append(heuristic_note("no_concrete_proposal_items"))
        return "Unresolved Gap", notes

    if proposal.section == "knowledge.concepts":
        notes.append(heuristic_note("non_critical_knowledge_extension"))
        return "Inferred Extension", notes

    notes.append(heuristic_note("section_change_requires_manual_review"))
    return "Authorized Transformation", notes
