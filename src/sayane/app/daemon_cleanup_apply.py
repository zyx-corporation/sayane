"""Conservative resident daemon cleanup apply."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.app.daemon_cleanup_decisions import build_cleanup_decision_report
from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_process_control import build_daemon_status_report
from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout
from sayane.app.daemon_stale_artifacts import build_stale_artifact_report


class ResidentDaemonCleanupApplyError(RuntimeError):
    """Structured cleanup-apply failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


class ResidentDaemonCleanupApplyTarget(StrEnum):
    """Allowed cleanup-apply targets for the MVP."""

    PID_FILE = "pid_file"
    LOCK_FILE = "lock_file"
    SOCKET_FILE = "socket_file"


@dataclass(frozen=True)
class ResidentDaemonCleanupApplyReceipt:
    """Cleanup-apply receipt."""

    operation_id: str
    runtime_root: Path
    requested_targets: tuple[str, ...]
    removed_paths: tuple[str, ...]
    result: str
    applied: bool
    failure_mode: str | None = None
    recovery_note: str | None = None
    created_at: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_cleanup_apply_receipt",
            "operation_id": self.operation_id,
            "runtime_root": str(self.runtime_root),
            "requested_targets": list(self.requested_targets),
            "removed_paths": list(self.removed_paths),
            "result": self.result,
            "applied": self.applied,
            "failure_mode": self.failure_mode,
            "recovery_note": self.recovery_note,
            "deletes_artifacts": self.applied,
            "mutates_filesystem": self.applied,
            "created_at": self.created_at or datetime.now(UTC).isoformat(),
        }


def _build_cleanup_decision_preview_payload(
    runtime_root: Path,
    *,
    host: str,
    port: int,
) -> dict[str, Any]:
    status = build_daemon_status_report(runtime_root, host=host, port=port).public_metadata()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    stale_report = build_stale_artifact_report(identity=identity, layout=layout)
    decision_report = build_cleanup_decision_report(stale_report).public_metadata()
    basis = {
        "runtime_root": str(runtime_root),
        "host": host,
        "port": port,
        "status": status,
        "decision_report": decision_report,
    }
    encoded = json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    preview_hash = hashlib.sha256(encoded).hexdigest()[:16]
    operation_id = f"cleanup-preview-{preview_hash[:12]}"
    return {
        "kind": "resident_daemon_cleanup_apply_preview",
        "runtime_root": str(runtime_root),
        "host": host,
        "port": port,
        "operation_id": operation_id,
        "preview_hash": preview_hash,
        "decision_report": decision_report,
        "status": status,
        "allowed_targets": [target.value for target in ResidentDaemonCleanupApplyTarget],
    }


def _build_cleanup_apply_payload(
    *,
    runtime_root: Path,
    requested_targets: tuple[str, ...],
    removed_paths: tuple[str, ...],
    result: str,
    applied: bool,
    failure_mode: str | None = None,
    recovery_note: str | None = None,
    operation_id: str | None = None,
    include_event_record: bool = False,
) -> dict[str, Any]:
    payload = ResidentDaemonCleanupApplyReceipt(
        operation_id=operation_id or f"daemon-cleanup-{uuid4().hex[:12]}",
        runtime_root=runtime_root,
        requested_targets=requested_targets,
        removed_paths=removed_paths,
        result=result,
        applied=applied,
        failure_mode=failure_mode,
        recovery_note=recovery_note,
    ).public_metadata()
    if include_event_record:
        from sayane.app.daemon_event_records import build_cleanup_apply_event_record

        payload["event_record"] = build_cleanup_apply_event_record(
            operation_id=payload["operation_id"],
            runtime_root=runtime_root,
            requested_targets=requested_targets,
            removed_paths=removed_paths,
            result=result,
            failure_mode=failure_mode,
            applied=applied,
        ).public_metadata()
    return payload


def apply_cleanup_decisions(
    runtime_root: Path,
    *,
    targets: tuple[ResidentDaemonCleanupApplyTarget, ...],
    host: str = "127.0.0.1",
    port: int = 38741,
    confirm_operation_id: str | None = None,
    confirm_preview_hash: str | None = None,
    include_event_record: bool = False,
) -> dict[str, Any]:
    """Apply conservative local cleanup to explicit runtime artifacts."""
    requested_targets = tuple(target.value for target in targets)
    preview_payload = _build_cleanup_decision_preview_payload(runtime_root, host=host, port=port)
    status = build_daemon_status_report(runtime_root, host=host, port=port)
    if status.is_running_daemon:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply is not allowed while the resident daemon is running",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="aborted",
                applied=False,
                failure_mode="daemon_running",
                recovery_note="Stop the resident daemon before cleanup apply.",
                include_event_record=include_event_record,
            ),
        )

    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    stale_report = build_stale_artifact_report(identity=identity, layout=layout)
    decision_report = build_cleanup_decision_report(stale_report).public_metadata()
    decisions = {decision["artifact_kind"]: decision for decision in decision_report["decisions"]}
    target_paths = {
        ResidentDaemonCleanupApplyTarget.PID_FILE: identity.pid_path,
        ResidentDaemonCleanupApplyTarget.LOCK_FILE: identity.lock_path,
        ResidentDaemonCleanupApplyTarget.SOCKET_FILE: identity.socket_path,
    }

    if not requested_targets:
        return _build_cleanup_apply_payload(
            runtime_root=runtime_root,
            requested_targets=(),
            removed_paths=(),
            result="no_action",
            applied=False,
            recovery_note="No cleanup targets were requested.",
            include_event_record=include_event_record,
        )

    if confirm_operation_id is None:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply requires explicit confirm_operation_id",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_operation_id_missing",
                recovery_note="Pass the cleanup preview operation_id to cleanup apply.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_preview_hash is None:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply requires explicit confirm_preview_hash",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_preview_hash_missing",
                recovery_note="Pass the cleanup preview hash to cleanup apply.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_operation_id != preview_payload["operation_id"]:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply confirm_operation_id must match the current preview",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_operation_id_mismatch",
                recovery_note=(
                    "Refresh daemon-cleanup-decisions and re-confirm the current preview."
                ),
                include_event_record=include_event_record,
            ),
        )
    if confirm_preview_hash != preview_payload["preview_hash"]:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply confirm_preview_hash must match the current preview",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_preview_hash_mismatch",
                recovery_note=(
                    "Refresh daemon-cleanup-decisions and re-confirm the current preview."
                ),
                include_event_record=include_event_record,
            ),
        )

    if status.manual_review_required and status.failure_mode not in {
        "stale_pid_file",
        "lock_without_pid",
    }:
        raise ResidentDaemonCleanupApplyError(
            "cleanup apply requires manual review for the current daemon state",
            payload=_build_cleanup_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                removed_paths=(),
                result="requires_review",
                applied=False,
                failure_mode=status.failure_mode,
                recovery_note="Resolve unexpected runtime state before cleanup apply.",
                include_event_record=include_event_record,
            ),
        )

    removed_paths: list[str] = []
    for target in targets:
        decision = decisions[target.value]
        if decision["recommendation"] == "unsafe_to_delete":
            raise ResidentDaemonCleanupApplyError(
                "cleanup apply target is unsafe to delete",
                payload=_build_cleanup_apply_payload(
                    runtime_root=runtime_root,
                    requested_targets=requested_targets,
                    removed_paths=tuple(removed_paths),
                    result="requires_review",
                    applied=False,
                    failure_mode=f"{target.value}_unsafe_to_delete",
                    recovery_note="Review the artifact type mismatch before deletion.",
                    include_event_record=include_event_record,
                ),
            )
        path = target_paths[target]
        if path.exists():
            path.unlink()
            removed_paths.append(str(path))

    return _build_cleanup_apply_payload(
        runtime_root=runtime_root,
        requested_targets=requested_targets,
        removed_paths=tuple(removed_paths),
        result="applied" if removed_paths else "no_action",
        applied=bool(removed_paths),
        recovery_note="Only explicitly requested file targets were removed.",
        include_event_record=include_event_record,
    )


def build_cleanup_apply_preview(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> dict[str, Any]:
    """Build the current cleanup-apply preview with confirmation fields."""
    return _build_cleanup_decision_preview_payload(runtime_root, host=host, port=port)
