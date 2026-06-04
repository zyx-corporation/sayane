"""Lineage types for Candidate Review audit trail."""

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

LineageOperation = Literal[
    "capture_created",
    "candidate_generated",
    "candidate_evaluated",
    "candidate_diffed",
    "candidate_approved",
    "candidate_rejected",
    "candidate_deferred",
    "candidate_revised",
    "context_written",
    "persona_ir_split",
]

LineageNodeKind = Literal[
    "capture",
    "candidate",
    "evaluation",
    "decision",
    "context_entry",
]

LineageActor = Literal["user", "system", "bridge", "llm"]


class LineageEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    operation: LineageOperation
    node_kind: LineageNodeKind
    timestamp: str
    actor: LineageActor = "bridge"
    capture_id: str | None = None
    candidate_id: str | None = None
    revised_candidate_id: str | None = None
    source_candidate_id: str | None = None
    context_path: str | None = None
    profile_id: str | None = None
    source_url: str | None = None
    source_kind: str | None = None
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class CandidateLineage(BaseModel):
    """Aggregated lineage for one capture/candidate."""

    model_config = ConfigDict(extra="forbid")

    capture_id: str
    candidate_id: str
    profile_id: str
    status: str
    evaluation_status: str | None = None
    rde_class: str | None = None
    section: str | None = None
    source_kind: str | None = None
    source_url: str | None = None
    captured_at: str
    decision: Literal["pending", "approved", "rejected", "deferred", "evaluated"] = "pending"
    context_path: str | None = None
    source_candidate_id: str | None = None
    revised_candidate_id: str | None = None
    operation: str | None = None
    events: list[LineageEvent] = Field(default_factory=list)
