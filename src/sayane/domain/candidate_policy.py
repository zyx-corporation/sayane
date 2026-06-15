"""Domain policy for Candidate lifecycle operations."""

from __future__ import annotations

from typing import Any

from sayane.core.candidate import CandidateUpdate
from sayane.evaluators.sections import CRITICAL_CONTEXT_SECTIONS, can_merge_section

UNSAFE_APPROVE_CATEGORIES = {
    "Preserved",
    "Unresolved Gap",
    "Suspicious Drift",
    "Critical Distortion",
}


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


def candidate_rde_category(candidate: CandidateUpdate) -> str | None:
    return candidate.evaluation.rde_class if candidate.evaluation else None


def ensure_can_evaluate(candidate: CandidateUpdate, candidate_id: str) -> None:
    if candidate.status in {"approved", "rejected"}:
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(f"This candidate is already {candidate.status} and cannot be evaluated."),
            candidate_id=candidate_id,
            status=candidate.status,
            rde_category=candidate_rde_category(candidate),
        )


def ensure_can_reject(candidate: CandidateUpdate, candidate_id: str) -> None:
    if candidate.status in {"approved", "rejected"}:
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(f"This candidate is already {candidate.status} and cannot be rejected."),
            candidate_id=candidate_id,
            status=candidate.status,
            rde_category=candidate_rde_category(candidate),
        )


def ensure_can_approve(
    candidate: CandidateUpdate,
    candidate_id: str,
    *,
    force_critical: bool = False,
    explicit_confirmation: dict[str, Any] | None = None,
) -> None:
    if candidate.status != "evaluated":
        raise CandidateOperationError(
            error="invalid_candidate_transition",
            message=(
                "This candidate is not in evaluated state and cannot be approved. "
                "Evaluate it first."
            ),
            candidate_id=candidate_id,
            status=candidate.status,
            rde_category=candidate_rde_category(candidate),
        )
    rde_category = candidate_rde_category(candidate)
    if rde_category in UNSAFE_APPROVE_CATEGORIES:
        critical_override = rde_category == "Critical Distortion" and force_critical
        if not critical_override:
            raise CandidateOperationError(
                error="unsafe_rde_category",
                message=(
                    f"This candidate is classified as {rde_category} "
                    "and cannot be approved directly."
                ),
                candidate_id=candidate_id,
                status=candidate.status,
                rde_category=rde_category,
            )
    section = candidate.proposal.section
    if section in CRITICAL_CONTEXT_SECTIONS:
        confirmation = explicit_confirmation or {}
        if not confirmation.get("checked"):
            raise CandidateOperationError(
                error="explicit_confirmation_required",
                message="Explicit confirmation is required for critical section merge.",
                candidate_id=candidate_id,
                status=candidate.status,
                rde_category=rde_category,
                section=section,
            )
        reason = (confirmation.get("reason") or "").strip()
        if not reason:
            raise CandidateOperationError(
                error="explicit_confirmation_reason_required",
                message="Explicit confirmation reason is required for critical section merge.",
                candidate_id=candidate_id,
                status=candidate.status,
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
            status=candidate.status,
            rde_category=rde_category,
            section=section,
        )
