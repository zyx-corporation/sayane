"""Build lineage views from candidates and jsonl audit records."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateUpdate
from sayane.lineage.models import (
    CandidateLineage,
    LineageActor,
    LineageEvent,
    LineageNodeKind,
    LineageOperation,
)
from sayane.storage.candidates import load_candidate
from sayane.storage.lineage_store import list_records


def _normalize_operation(raw_event: str, payload: dict[str, Any]) -> LineageOperation:
    op = payload.get("operation")
    if isinstance(op, str) and op:
        return op  # type: ignore[return-value]
    if raw_event in (
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
    ):
        return raw_event  # type: ignore[return-value]
    if raw_event == "candidate_approved":
        return "candidate_approved"
    if raw_event == "candidate_rejected":
        return "candidate_rejected"
    return "candidate_generated"


def _node_kind_for_operation(operation: LineageOperation) -> LineageNodeKind:
    if operation in ("capture_created",):
        return "capture"
    if operation in ("candidate_generated", "candidate_revised"):
        return "candidate"
    if operation in ("candidate_evaluated", "candidate_diffed"):
        return "evaluation"
    if operation in ("candidate_approved", "candidate_rejected", "candidate_deferred"):
        return "decision"
    return "context_entry"


def _record_to_event(raw: dict[str, Any]) -> LineageEvent | None:
    raw_event = str(raw.get("event", ""))
    if not raw_event:
        return None
    operation = _normalize_operation(raw_event, raw)
    node_kind = raw.get("node_kind")
    if node_kind not in (
        "capture",
        "candidate",
        "evaluation",
        "decision",
        "context_entry",
    ):
        node_kind = _node_kind_for_operation(operation)
    actor = raw.get("actor")
    if actor not in ("user", "system", "bridge", "llm"):
        actor = "bridge"
    metadata = raw.get("metadata")
    if not isinstance(metadata, dict):
        metadata = {
            k: v
            for k, v in raw.items()
            if k
            not in {
                "event",
                "at",
                "operation",
                "node_kind",
                "actor",
                "event_id",
                "capture_id",
                "candidate_id",
                "source_candidate_id",
                "revised_candidate_id",
                "context_path",
                "profile_id",
                "source_url",
                "source_kind",
                "note",
                "metadata",
            }
        }
    return LineageEvent(
        id=str(raw.get("event_id") or uuid4().hex),
        operation=operation,
        node_kind=node_kind,  # type: ignore[arg-type]
        timestamp=str(raw.get("at", "")),
        actor=actor,  # type: ignore[arg-type]
        capture_id=raw.get("capture_id") or raw.get("candidate_id"),
        candidate_id=raw.get("candidate_id"),
        source_candidate_id=raw.get("source_candidate_id"),
        revised_candidate_id=raw.get("revised_candidate_id"),
        context_path=raw.get("context_path") or raw.get("section"),
        profile_id=raw.get("profile_id"),
        source_url=raw.get("source_url"),
        source_kind=raw.get("source_kind"),
        note=raw.get("note") or raw.get("reason"),
        metadata=metadata,
    )


def _synthetic_events(candidate: CandidateUpdate) -> list[LineageEvent]:
    """Events implied by current candidate state when not yet in jsonl."""
    events: list[LineageEvent] = []
    capture_id = candidate.id
    captured_at = candidate.source.captured_at.isoformat()
    source_kind = (
        candidate.capture_meta.capture_source
        if candidate.capture_meta
        else "page"
    )
    events.append(
        LineageEvent(
            id=f"synth-capture-{capture_id}",
            operation="capture_created",
            node_kind="capture",
            timestamp=captured_at,
            actor="system",
            capture_id=capture_id,
            candidate_id=capture_id,
            profile_id=candidate.target_profile_id,
            source_url=candidate.source.uri,
            source_kind=source_kind,
        ),
    )
    events.append(
        LineageEvent(
            id=f"synth-generated-{capture_id}",
            operation="candidate_generated",
            node_kind="candidate",
            timestamp=captured_at,
            actor="bridge",
            capture_id=capture_id,
            candidate_id=capture_id,
            profile_id=candidate.target_profile_id,
            source_url=candidate.source.uri,
            source_kind=source_kind,
            metadata={"section": candidate.proposal.section},
        ),
    )
    if candidate.evaluation:
        events.append(
            LineageEvent(
                id=f"synth-evaluated-{capture_id}",
                operation="candidate_evaluated",
                node_kind="evaluation",
                timestamp=candidate.evaluation.evaluated_at.isoformat(),
                actor="llm" if candidate.evaluation.llm_review else "bridge",
                capture_id=capture_id,
                candidate_id=capture_id,
                profile_id=candidate.target_profile_id,
                metadata={
                    "rde_class": candidate.evaluation.rde_class,
                    "level": candidate.evaluation.level,
                },
            ),
        )
    if candidate.status == "approved":
        events.append(
            LineageEvent(
                id=f"synth-approved-{capture_id}",
                operation="candidate_approved",
                node_kind="decision",
                timestamp=captured_at,
                actor="user",
                capture_id=capture_id,
                candidate_id=capture_id,
                context_path=candidate.proposal.section,
                profile_id=candidate.target_profile_id,
            ),
        )
        events.append(
            LineageEvent(
                id=f"synth-context-{capture_id}",
                operation="context_written",
                node_kind="context_entry",
                timestamp=captured_at,
                actor="bridge",
                capture_id=capture_id,
                candidate_id=capture_id,
                context_path=candidate.proposal.section,
                profile_id=candidate.target_profile_id,
            ),
        )
    elif candidate.status == "rejected":
        events.append(
            LineageEvent(
                id=f"synth-rejected-{capture_id}",
                operation="candidate_rejected",
                node_kind="decision",
                timestamp=captured_at,
                actor="user",
                capture_id=capture_id,
                candidate_id=capture_id,
                profile_id=candidate.target_profile_id,
            ),
        )
    return events


def _merge_events(
    synthetic: list[LineageEvent],
    stored: list[LineageEvent],
) -> list[LineageEvent]:
    """Prefer stored jsonl events; fill gaps from synthetic state."""
    by_op: dict[LineageOperation, LineageEvent] = {}
    for event in synthetic:
        by_op[event.operation] = event
    for event in stored:
        by_op[event.operation] = event
    merged = list(by_op.values())
    merged.sort(key=lambda e: e.timestamp)
    return merged


def _decision_from_candidate(candidate: CandidateUpdate) -> str:
    if candidate.status == "approved":
        return "approved"
    if candidate.status == "rejected":
        return "rejected"
    if candidate.status == "evaluated":
        return "evaluated"
    return "pending"


def build_candidate_lineage(
    config: BridgeConfig,
    candidate_id: str,
) -> CandidateLineage:
    candidate = load_candidate(config, candidate_id)
    profile_id = candidate.target_profile_id
    records = list_records(config, profile_id, limit=500)
    stored_events: list[LineageEvent] = []
    for raw in records:
        cid = raw.get("candidate_id")
        if cid != candidate_id:
            continue
        event = _record_to_event(raw)
        if event:
            stored_events.append(event)

    synthetic = _synthetic_events(candidate)
    events = _merge_events(synthetic, stored_events)

    context_path = None
    for event in reversed(events):
        if event.context_path:
            context_path = event.context_path
            break
    if not context_path:
        context_path = candidate.proposal.section

    source_kind = (
        candidate.capture_meta.capture_source
        if candidate.capture_meta
        else None
    )
    rde = candidate.evaluation.rde_class if candidate.evaluation else None

    # Collect operation from events metadata for display.
    operation = None
    for event in events:
        if isinstance(event.metadata, dict) and event.metadata.get("operation"):
            operation = str(event.metadata["operation"])
            break

    return CandidateLineage(
        capture_id=candidate.id,
        candidate_id=candidate.id,
        profile_id=profile_id,
        status=candidate.status,
        evaluation_status=candidate.evaluation_status,
        rde_class=rde,
        section=candidate.proposal.section,
        source_kind=source_kind,
        source_url=candidate.source.uri,
        captured_at=candidate.source.captured_at.isoformat(),
        decision=_decision_from_candidate(candidate),  # type: ignore[arg-type]
        context_path=context_path if candidate.status == "approved" else None,
        source_candidate_id=(
            candidate.parent_capture_id
            or (candidate.storage_policy.target_path if candidate.storage_policy else None)
            or None
        ),
        events=events,
        operation=operation,
    )


def build_capture_lineage(config: BridgeConfig, capture_id: str) -> CandidateLineage:
    """v1: capture id equals candidate id."""
    return build_candidate_lineage(config, capture_id)
