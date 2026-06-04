"""Append normalized lineage events to the profile jsonl store."""

from typing import Any
from uuid import uuid4

from sayane.bridge.config import BridgeConfig
from sayane.lineage.models import LineageActor, LineageNodeKind, LineageOperation
from sayane.storage.lineage_store import append_record


def record_lineage_event(
    config: BridgeConfig,
    profile_id: str,
    *,
    operation: LineageOperation,
    node_kind: LineageNodeKind,
    actor: LineageActor = "bridge",
    capture_id: str | None = None,
    candidate_id: str | None = None,
    source_candidate_id: str | None = None,
    revised_candidate_id: str | None = None,
    context_path: str | None = None,
    source_url: str | None = None,
    source_kind: str | None = None,
    note: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> None:
    """Persist one lineage event (append-only)."""
    payload: dict[str, Any] = {
        "operation": operation,
        "node_kind": node_kind,
        "actor": actor,
        "event_id": uuid4().hex,
    }
    if capture_id:
        payload["capture_id"] = capture_id
    if candidate_id:
        payload["candidate_id"] = candidate_id
    if source_candidate_id:
        payload["source_candidate_id"] = source_candidate_id
    if revised_candidate_id:
        payload["revised_candidate_id"] = revised_candidate_id
    if context_path:
        payload["context_path"] = context_path
    if source_url:
        payload["source_url"] = source_url
    if source_kind:
        payload["source_kind"] = source_kind
    if note:
        payload["note"] = note
    if metadata:
        payload["metadata"] = metadata
    append_record(config, profile_id, operation, payload)
