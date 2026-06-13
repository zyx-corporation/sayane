"""Candidate Review Decision Model and Lineage (Phase 7, F-1.5).

Review decisions connect semantic review metadata to human decisions.
Auto-approve and auto-reject are forbidden.
All decisions are recorded in lineage.

F-1.5: scoped_accept adds scope, conditions, negative constraints,
promotion policy, and reuse policy for conditional partial context acceptance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal
from uuid import uuid4

ReviewDecisionType = Literal["approve", "reject", "modify", "defer", "scoped_accept"]


@dataclass
class ReviewDecision:
    """A human review decision on a candidate."""

    candidate_id: str
    decision: ReviewDecisionType
    reason: str = ""
    reviewer: str = "local_user"
    decided_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    applied_value: Any = None
    original_section: str = ""
    original_action: str = ""
    original_proposed: Any = None
    # Semantic review context from Phase 6
    review_flags: list[str] = field(default_factory=list)
    review_warnings: list[dict[str, Any]] = field(default_factory=list)
    overlap_groups: list[str] = field(default_factory=list)
    # Lineage tracking
    lineage_event_id: str = field(default_factory=lambda: uuid4().hex)
    transfer_path: list[str] = field(default_factory=list)
    # Scoped accept (F-1.5)
    source_scope: dict[str, Any] | None = None
    proposed_scope: dict[str, Any] | None = None
    accepted_scope: dict[str, Any] | None = None
    conditions: list[str] = field(default_factory=list)
    negative_constraints: list[str] = field(default_factory=list)
    promotion_policy: dict[str, Any] | None = None
    reuse_policy: dict[str, Any] | None = None


# --- Review decision store (in-memory for CLI; Bridge uses candidate storage) ---

_decisions: dict[str, list[ReviewDecision]] = {}


def save_decision(profile_id: str, decision: ReviewDecision) -> None:
    """Persist a review decision."""
    if profile_id not in _decisions:
        _decisions[profile_id] = []
    _decisions[profile_id].append(decision)


def list_decisions(profile_id: str = "default") -> list[ReviewDecision]:
    """List all review decisions for a profile."""
    return list(_decisions.get(profile_id, []))


def load_review_decisions(
    profile_id: str = "default",
    project_id: str | None = None,
) -> list[ReviewDecision]:
    """Load review decisions for MCP compiled context.

    This is the storage adapter for MCP context compilation.
    It does NOT decide what to expose — that is deferred to
    filter_mcp_exposable_candidates() in mcp_context.py.

    Returns all decisions; callers must apply exposure policy.
    """
    decisions = list(_decisions.get(profile_id, []))
    # Future: filter by project_id when project-scoped lineage is implemented
    _ = project_id
    return list(decisions)


def clear_decisions(profile_id: str = "default") -> None:
    """Clear all decisions for a profile (test helper)."""
    _decisions.pop(profile_id, None)


def get_decisions_for_candidate(candidate_id: str, profile_id: str = "default") -> list[ReviewDecision]:
    """Get decisions affecting a specific candidate."""
    return [d for d in _decisions.get(profile_id, []) if d.candidate_id == candidate_id]


# --- Overlap group resolution ---

@dataclass
class OverlapResolution:
    overlap_id: str
    terms: list[str]
    candidate_ids: list[str]
    resolved: bool = False
    resolution_reason: str = ""
    resolved_at: str = ""
    decisions: list[str] = field(default_factory=list)


_overlap_resolutions: dict[str, OverlapResolution] = {}


def record_overlap_resolution(resolution: OverlapResolution) -> None:
    _overlap_resolutions[resolution.overlap_id] = resolution


def get_overlap_resolution(overlap_id: str) -> OverlapResolution | None:
    return _overlap_resolutions.get(overlap_id)


# --- Validation ---

def validate_decision(decision: ReviewDecision, has_review_required: bool) -> list[str]:
    """Validate a review decision. Returns list of errors (empty = valid)."""
    errors: list[str] = []

    if decision.decision == "approve" and has_review_required and not decision.reason.strip():
        errors.append("review_required candidates require an explicit reason for approval")

    if decision.decision == "modify" and decision.applied_value is None:
        errors.append("modify decision requires applied_value")

    if decision.decision == "scoped_accept":
        if not decision.reason.strip():
            errors.append("scoped_accept requires an explicit reason")
        if decision.accepted_scope is None:
            errors.append("scoped_accept requires accepted_scope")

    return errors


# --- Lineage event generation ---

def build_lineage_event(decision: ReviewDecision) -> dict[str, Any]:
    """Build a lineage event dict from a review decision."""
    event: dict[str, Any] = {
        "id": decision.lineage_event_id,
        "type": "candidate_review_decision",
        "created_at": decision.decided_at,
        "reviewer": decision.reviewer,
        "candidate": {
            "id": decision.candidate_id,
            "section": decision.original_section,
            "action": decision.original_action,
            "proposed": decision.original_proposed,
        },
        "semantic_review": {
            "flags": decision.review_flags,
            "warnings": decision.review_warnings,
            "overlap_groups": decision.overlap_groups,
        },
        "decision": {
            "type": decision.decision,
            "reason": decision.reason,
            "applied_value": decision.applied_value,
        },
        "transfer_path": decision.transfer_path,
    }

    # Scoped accept metadata (F-1.5)
    if decision.decision == "scoped_accept":
        event["scoped_accept"] = {
            "source_scope": decision.source_scope,
            "accepted_scope": decision.accepted_scope,
            "conditions": decision.conditions,
            "negative_constraints": decision.negative_constraints,
            "promotion_policy": decision.promotion_policy or {"can_promote": False},
            "reuse_policy": decision.reuse_policy or {"review_on_reuse": True},
        }

    return event
