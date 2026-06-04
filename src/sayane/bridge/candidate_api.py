"""Bridge handlers for Candidate evaluate / approve flow."""

from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateUpdate
from sayane.evaluators.sections import CRITICAL_CONTEXT_SECTIONS, can_merge_section
from sayane.evaluators.list_diff import important_terms_display_summary
from sayane.evaluators.service import (
    approve_candidate,
    diff_candidate,
    evaluate_candidate,
    reject_candidate,
)
from sayane.storage.candidates import list_candidate_ids, load_candidate


class CandidateOperationError(ValueError):
    """Client-safe error for invalid candidate operations."""

    def __init__(
        self,
        *,
        error: str,
        message: str,
        candidate_id: str,
        status: str | None = None,
        rde_category: str | None = None,
        section: str | None = None,
    ) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.candidate_id = candidate_id
        self.status = status
        self.rde_category = rde_category
        self.section = section

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "error": self.error,
            "message": self.message,
            "candidate_id": self.candidate_id,
        }
        if self.status:
            payload["status"] = self.status
        if self.rde_category:
            payload["rde_category"] = self.rde_category
        if self.section:
            payload["section"] = self.section
        return payload


UNSAFE_APPROVE_CATEGORIES = {
    "Preserved",
    "Unresolved Gap",
    "Suspicious Drift",
    "Critical Distortion",
}


def list_candidates(config: BridgeConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for cid in list_candidate_ids(config):
        try:
            c = load_candidate(config, cid)
            items.append(_candidate_summary(c))
        except Exception:
            continue
    return items


def get_candidate(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    candidate = load_candidate(config, candidate_id)
    data = candidate.model_dump(mode="json")
    data["source_excerpt"] = _source_excerpt(candidate)
    return data


def post_evaluate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    level: int = 1,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    if existing.status in {"approved", "rejected"}:
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(
                f"This candidate is already {existing.status} "
                "and cannot be evaluated."
            ),
            candidate_id=candidate_id,
            status=existing.status,
            rde_category=(
                existing.evaluation.rde_class if existing.evaluation else None
            ),
        )
    candidate = evaluate_candidate(config, candidate_id, level=level)
    return candidate.model_dump(mode="json")


def post_approve(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
    override_reason: str | None = None,
    explicit_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    if existing.status != "evaluated":
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(
                "This candidate is not in evaluated state and cannot be approved. "
                "Evaluate it first."
            ),
            candidate_id=candidate_id,
            status=existing.status,
            rde_category=(
                existing.evaluation.rde_class if existing.evaluation else None
            ),
        )
    rde_category = existing.evaluation.rde_class if existing.evaluation else None
    if rde_category in UNSAFE_APPROVE_CATEGORIES:
        critical_override = (
            rde_category == "Critical Distortion" and force_critical
        )
        if not critical_override:
            raise CandidateOperationError(
                error="unsafe_rde_category",
                message=(
                    f"This candidate is classified as {rde_category} "
                    "and cannot be approved directly."
                ),
                candidate_id=candidate_id,
                status=existing.status,
                rde_category=rde_category,
            )
    section = existing.proposal.section
    if section in CRITICAL_CONTEXT_SECTIONS:
        ec = explicit_confirmation or {}
        if not ec.get("checked"):
            raise CandidateOperationError(
                error="explicit_confirmation_required",
                message=(
                    "Explicit confirmation is required for critical section merge."
                ),
                candidate_id=candidate_id,
                status=existing.status,
                rde_category=rde_category,
                section=section,
            )
        reason = (ec.get("reason") or "").strip()
        if not reason:
            raise CandidateOperationError(
                error="explicit_confirmation_reason_required",
                message=(
                    "Explicit confirmation reason is required for critical section merge."
                ),
                candidate_id=candidate_id,
                status=existing.status,
                rde_category=rde_category,
                section=section,
            )
    if not can_merge_section(section, force_critical=force_critical):
        raise CandidateOperationError(
            error="requires_force_critical",
            message=(
                f"Cannot merge section '{section}' without force_critical. "
                "Confirm in the review panel after checking the diff."
            ),
            candidate_id=candidate_id,
            status=existing.status,
            rde_category=rde_category,
            section=section,
        )
    candidate = approve_candidate(
        config,
        candidate_id,
        force_critical=force_critical,
        override_reason=override_reason,
    )
    return candidate.model_dump(mode="json")


def post_reject(
    config: BridgeConfig,
    candidate_id: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    if existing.status in {"approved", "rejected"}:
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(
                f"This candidate is already {existing.status} "
                "and cannot be rejected."
            ),
            candidate_id=candidate_id,
            status=existing.status,
            rde_category=(
                existing.evaluation.rde_class if existing.evaluation else None
            ),
        )
    candidate = reject_candidate(config, candidate_id, reason=reason)
    return candidate.model_dump(mode="json")


def get_diff(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    return diff_candidate(config, candidate_id)


def get_candidate_lineage(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    from sayane.lineage.query import build_candidate_lineage

    lineage = build_candidate_lineage(config, candidate_id)
    return lineage.model_dump(mode="json")


def get_capture_lineage(config: BridgeConfig, capture_id: str) -> dict[str, Any]:
    from sayane.lineage.query import build_capture_lineage

    lineage = build_capture_lineage(config, capture_id)
    return lineage.model_dump(mode="json")


def _source_excerpt(c: CandidateUpdate, max_len: int = 1200) -> str:
    """Raw capture input for UI — never stored Profile IR (`content` field)."""
    text = (c.raw_capture or c.cleaned_capture or "").strip()
    if not text:
        text = (c.display_summary or "").strip()
    if len(text) > max_len:
        return text[:max_len]
    return text


def _capture_preview_text(c: CandidateUpdate) -> str:
    """Card list preview — prefer diff summary for list sections."""
    if c.proposal.section == "important_terms":
        summary = important_terms_display_summary(c.proposal, locale=c.locale)
        if summary:
            return summary[:200] + ("..." if len(summary) > 200 else "")
    source = _source_excerpt(c, max_len=200)
    if len(source) <= 200:
        return source
    return source[:200] + "..."


def _candidate_summary(c: CandidateUpdate) -> dict[str, Any]:
    return {
        "id": c.id,
        "status": c.status,
        "evaluation_status": c.evaluation_status,
        "evaluation_error": c.evaluation_error.model_dump(mode="json")
        if c.evaluation_error
        else None,
        "locale": c.locale,
        "target_profile_id": c.target_profile_id,
        "source": c.source.type,
        "source_url": c.source.uri,
        "captured_at": c.source.captured_at.isoformat(),
        "rde_class": c.evaluation.rde_class if c.evaluation else None,
        "evaluation_level": c.evaluation.level if c.evaluation else None,
        "section": c.proposal.section,
        "content_preview": _capture_preview_text(c),
        "display_summary": c.display_summary,
        "capture_source": (
            c.capture_meta.capture_source if c.capture_meta else c.source.type
        ),
    }
