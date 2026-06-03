"""Bridge handlers for Candidate evaluate / approve flow."""

from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateUpdate
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
    ) -> None:
        super().__init__(message)
        self.error = error
        self.message = message
        self.candidate_id = candidate_id
        self.status = status
        self.rde_category = rde_category

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
    return load_candidate(config, candidate_id).model_dump(mode="json")


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


def _candidate_summary(c: CandidateUpdate) -> dict[str, Any]:
    preview = c.content if len(c.content) <= 200 else c.content[:200] + "..."
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
        "content_preview": preview,
    }
