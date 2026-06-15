"""Bridge presentation helpers for Candidate payloads."""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import CandidateUpdate
from sayane.evaluators.list_diff import important_terms_display_summary


def source_excerpt(candidate: CandidateUpdate, max_len: int = 1200) -> str:
    """Raw capture input for UI — never stored Profile IR (`content` field)."""
    text = (candidate.raw_capture or candidate.cleaned_capture or "").strip()
    if not text:
        text = (candidate.display_summary or "").strip()
    if len(text) > max_len:
        return text[:max_len]
    return text


def capture_preview_text(candidate: CandidateUpdate) -> str:
    """Card list preview — prefer diff summary for list sections."""
    if candidate.proposal.section == "important_terms":
        summary = important_terms_display_summary(candidate.proposal, locale=candidate.locale)
        if summary:
            return summary[:200] + ("..." if len(summary) > 200 else "")
    source = source_excerpt(candidate, max_len=200)
    if len(source) <= 200:
        return source
    return source[:200] + "..."


def candidate_summary(candidate: CandidateUpdate) -> dict[str, Any]:
    return {
        "id": candidate.id,
        "status": candidate.status,
        "evaluation_status": candidate.evaluation_status,
        "evaluation_error": candidate.evaluation_error.model_dump(mode="json")
        if candidate.evaluation_error
        else None,
        "locale": candidate.locale,
        "target_profile_id": candidate.target_profile_id,
        "source": candidate.source.type,
        "source_url": candidate.source.uri,
        "captured_at": candidate.source.captured_at.isoformat(),
        "rde_class": candidate.evaluation.rde_class if candidate.evaluation else None,
        "evaluation_level": candidate.evaluation.level if candidate.evaluation else None,
        "section": candidate.proposal.section,
        "content_preview": capture_preview_text(candidate),
        "display_summary": candidate.display_summary,
        "capture_source": (
            candidate.capture_meta.capture_source if candidate.capture_meta else candidate.source.type
        ),
        "proposal_operation": candidate.proposal.operation,
        "storage_policy": candidate.storage_policy.model_dump(mode="json") if candidate.storage_policy else None,
        "parent_capture_id": candidate.parent_capture_id,
    }
