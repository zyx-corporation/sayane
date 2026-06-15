"""Important-terms YAML classification."""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import CandidateProposal
from sayane.core.models import SayaneProfile
from sayane.evaluators.important_terms_fragment import normalize_scalar
from sayane.evaluators.list_diff import (
    important_terms_display_summary,
    important_terms_profile_diff,
)

SECTION_REVIEW_REQUIRED = "review_required"
OPERATION_PARSE_FAILED = "parse_failed"
OPERATION_NO_EFFECTIVE = "parse_failed_or_no_effective_update"


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


def classify_important_terms_yaml(parsed: dict[str, Any], profile: SayaneProfile | None) -> CandidateProposal:
    terms_raw = parsed.get("important_terms")
    if not isinstance(terms_raw, list):
        return build_parse_failed_proposal("important_terms must be a YAML list")
    captured = [normalize_scalar(entry) for entry in terms_raw if normalize_scalar(entry)]
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
