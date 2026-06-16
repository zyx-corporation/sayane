"""Minimal resident UI review queue and MCP preview skeleton (#181)."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from sayane.app.capabilities import CapabilityToken
from sayane.core.candidate import CandidateUpdate
from sayane.core.mcp_context import build_compiled_context, build_mcp_exposure_denial
from sayane.core.review_decision import ReviewDecision
from sayane.storage.repositories import RepositoryBundle


def build_review_queue(
    repositories: RepositoryBundle,
    *,
    capability: CapabilityToken,
    include_statuses: tuple[str, ...] = ("pending", "evaluated"),
) -> dict[str, Any]:
    """Build a minimal Candidate review queue payload for resident UI.

    This is a review surface, not an MCP context export path.
    """
    capability.require("ui")
    decisions = repositories.review_decisions.list()
    latest_decisions = _latest_decision_by_candidate(decisions)
    candidates = [
        candidate
        for candidate in repositories.candidates.list()
        if candidate.status in include_statuses
    ]
    candidates.sort(key=lambda candidate: candidate.source.captured_at.isoformat())
    return {
        "profile_id": repositories.profile_id,
        "kind": "resident_review_queue",
        "is_review_surface": True,
        "is_mcp_context": False,
        "items": [
            _candidate_to_review_item(candidate, latest_decisions.get(candidate.id))
            for candidate in candidates
        ],
    }


def build_mcp_preview(
    repositories: RepositoryBundle,
    *,
    capability: CapabilityToken,
    mode: str = "full",
) -> dict[str, Any]:
    """Build an explicit resident UI preview of MCP compiled context.

    The preview is derived context. It must not become canonical profile state.
    Pending Candidate content remains blocked from normal context.
    """
    capability.require("mcp")
    decisions = repositories.review_decisions.list()
    compiled = build_compiled_context(
        profile_id=repositories.profile_id,
        mode=mode,
        scoped_decisions=decisions,
    )
    decided_candidate_ids = {decision.candidate_id for decision in decisions}
    pending_candidates = [
        candidate
        for candidate in repositories.candidates.list()
        if candidate.id not in decided_candidate_ids
    ]
    for candidate in pending_candidates:
        compiled["blocked_candidates"].append(
            build_mcp_exposure_denial(
                "candidate_not_reviewed",
                candidate_id=candidate.id,
                exposure_class="pending_candidate",
            )
        )
    compiled["preview"] = {
        "kind": "resident_mcp_preview",
        "is_preview": True,
        "is_derived_context": True,
        "is_canonical_profile": False,
    }
    return compiled


def _latest_decision_by_candidate(
    decisions: list[ReviewDecision],
) -> dict[str, ReviewDecision]:
    latest: dict[str, ReviewDecision] = {}
    for decision in decisions:
        latest[decision.candidate_id] = decision
    return latest


def _candidate_to_review_item(
    candidate: CandidateUpdate,
    decision: ReviewDecision | None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate.id,
        "status": candidate.status,
        "evaluation_status": candidate.evaluation_status,
        "target_profile_id": candidate.target_profile_id,
        "source_type": candidate.source.type,
        "captured_at": candidate.source.captured_at.isoformat(),
        "proposal_section": candidate.proposal.section,
        "proposal_operation": candidate.proposal.operation,
        "display_summary": candidate.display_summary or candidate.proposal.summary,
        "capture_source": (
            candidate.capture_meta.capture_source if candidate.capture_meta is not None else None
        ),
        "requires_review": (
            candidate.capture_meta.requires_review if candidate.capture_meta is not None else False
        ),
        "latest_decision": asdict(decision) if decision is not None else None,
    }
