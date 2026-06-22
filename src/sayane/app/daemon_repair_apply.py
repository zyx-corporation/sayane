"""Conservative resident daemon repair apply."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.app.daemon_process_control import build_daemon_status_report
from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout


class ResidentDaemonRepairApplyError(RuntimeError):
    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


class ResidentDaemonRepairApplyTarget(StrEnum):
    RUNTIME_ROOT = "runtime_root"
    PID_DIR = "pid_dir"
    LOCK_DIR = "lock_dir"
    SOCKET_DIR = "socket_dir"
    LOG_DIR = "log_dir"
    TEMP_DIR = "temp_dir"
    STATE_DIR = "state_dir"


@dataclass(frozen=True)
class ResidentDaemonRepairApplyReceipt:
    operation_id: str
    runtime_root: Path
    requested_targets: tuple[str, ...]
    created_paths: tuple[str, ...]
    result: str
    applied: bool
    failure_mode: str | None = None
    recovery_note: str | None = None
    created_at: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_repair_apply_receipt",
            "operation_id": self.operation_id,
            "runtime_root": str(self.runtime_root),
            "requested_targets": list(self.requested_targets),
            "created_paths": list(self.created_paths),
            "result": self.result,
            "applied": self.applied,
            "failure_mode": self.failure_mode,
            "recovery_note": self.recovery_note,
            "creates_artifacts": self.applied,
            "mutates_filesystem": self.applied,
            "created_at": self.created_at or datetime.now(UTC).isoformat(),
        }


def _repair_targets(
    layout: ResidentDaemonRuntimeLayout,
) -> dict[ResidentDaemonRepairApplyTarget, Path]:
    return {
        ResidentDaemonRepairApplyTarget.RUNTIME_ROOT: layout.runtime_root,
        ResidentDaemonRepairApplyTarget.PID_DIR: layout.pid_dir,
        ResidentDaemonRepairApplyTarget.LOCK_DIR: layout.lock_dir,
        ResidentDaemonRepairApplyTarget.SOCKET_DIR: layout.socket_dir,
        ResidentDaemonRepairApplyTarget.LOG_DIR: layout.log_dir,
        ResidentDaemonRepairApplyTarget.TEMP_DIR: layout.temp_dir,
        ResidentDaemonRepairApplyTarget.STATE_DIR: layout.state_dir,
    }


def _inspect_target(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"status": "missing", "repairable": True}
    if path.is_symlink():
        return {"status": "review_required", "repairable": False}
    if path.is_dir():
        return {"status": "no_action", "repairable": False}
    return {"status": "review_required", "repairable": False}


def _build_repair_preview_payload(runtime_root: Path, *, host: str, port: int) -> dict[str, Any]:
    status = build_daemon_status_report(runtime_root, host=host, port=port).public_metadata()
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    decisions = {
        target.value: {"path": str(path), **_inspect_target(path)}
        for target, path in _repair_targets(layout).items()
    }
    basis = {
        "runtime_root": str(runtime_root),
        "host": host,
        "port": port,
        "status": status,
        "decisions": decisions,
    }
    encoded = json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
    preview_hash = hashlib.sha256(encoded).hexdigest()[:16]
    return {
        "kind": "resident_daemon_repair_apply_preview",
        "runtime_root": str(runtime_root),
        "host": host,
        "port": port,
        "operation_id": f"repair-preview-{preview_hash[:12]}",
        "preview_hash": preview_hash,
        "status": status,
        "decisions": decisions,
        "allowed_targets": [target.value for target in ResidentDaemonRepairApplyTarget],
    }


def _build_repair_apply_payload(
    *,
    runtime_root: Path,
    requested_targets: tuple[str, ...],
    created_paths: tuple[str, ...],
    result: str,
    applied: bool,
    failure_mode: str | None = None,
    recovery_note: str | None = None,
    include_event_record: bool = False,
    operation_id: str | None = None,
) -> dict[str, Any]:
    payload = ResidentDaemonRepairApplyReceipt(
        operation_id=operation_id or f"daemon-repair-{uuid4().hex[:12]}",
        runtime_root=runtime_root,
        requested_targets=requested_targets,
        created_paths=created_paths,
        result=result,
        applied=applied,
        failure_mode=failure_mode,
        recovery_note=recovery_note,
    ).public_metadata()
    if include_event_record:
        from sayane.app.daemon_event_records import build_repair_apply_event_record

        payload["event_record"] = build_repair_apply_event_record(
            operation_id=payload["operation_id"],
            runtime_root=runtime_root,
            requested_targets=requested_targets,
            created_paths=created_paths,
            result=result,
            failure_mode=failure_mode,
            applied=applied,
        ).public_metadata()
    return payload


def build_repair_apply_preview(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> dict[str, Any]:
    return _build_repair_preview_payload(runtime_root, host=host, port=port)


def apply_runtime_repairs(
    runtime_root: Path,
    *,
    targets: tuple[ResidentDaemonRepairApplyTarget, ...],
    host: str = "127.0.0.1",
    port: int = 38741,
    confirm_operation_id: str | None = None,
    confirm_preview_hash: str | None = None,
    include_event_record: bool = False,
) -> dict[str, Any]:
    requested_targets = tuple(target.value for target in targets)
    preview_payload = _build_repair_preview_payload(runtime_root, host=host, port=port)
    status = build_daemon_status_report(runtime_root, host=host, port=port)
    if not requested_targets:
        return _build_repair_apply_payload(
            runtime_root=runtime_root,
            requested_targets=(),
            created_paths=(),
            result="no_action",
            applied=False,
            recovery_note="No repair targets were requested.",
            include_event_record=include_event_record,
        )
    if status.is_running_daemon:
        raise ResidentDaemonRepairApplyError(
            "repair apply is not allowed while the resident daemon is running",
            payload=_build_repair_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                created_paths=(),
                result="aborted",
                applied=False,
                failure_mode="daemon_running",
                recovery_note="Stop the resident daemon before repair apply.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_operation_id is None:
        raise ResidentDaemonRepairApplyError(
            "repair apply requires explicit confirm_operation_id",
            payload=_build_repair_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                created_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_operation_id_missing",
                recovery_note="Pass the repair preview operation_id to repair apply.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_preview_hash is None:
        raise ResidentDaemonRepairApplyError(
            "repair apply requires explicit confirm_preview_hash",
            payload=_build_repair_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                created_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_preview_hash_missing",
                recovery_note="Pass the repair preview hash to repair apply.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_operation_id != preview_payload["operation_id"]:
        raise ResidentDaemonRepairApplyError(
            "repair apply confirm_operation_id must match the current preview",
            payload=_build_repair_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                created_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_operation_id_mismatch",
                recovery_note="Refresh daemon-repair-preview and re-confirm the current preview.",
                include_event_record=include_event_record,
            ),
        )
    if confirm_preview_hash != preview_payload["preview_hash"]:
        raise ResidentDaemonRepairApplyError(
            "repair apply confirm_preview_hash must match the current preview",
            payload=_build_repair_apply_payload(
                runtime_root=runtime_root,
                requested_targets=requested_targets,
                created_paths=(),
                result="aborted",
                applied=False,
                failure_mode="confirm_preview_hash_mismatch",
                recovery_note="Refresh daemon-repair-preview and re-confirm the current preview.",
                include_event_record=include_event_record,
            ),
        )
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    target_paths = _repair_targets(layout)
    decisions: dict[str, dict[str, Any]] = preview_payload["decisions"]
    created_paths: list[str] = []
    for target in targets:
        decision = decisions[target.value]
        if not decision["repairable"] and decision["status"] != "missing":
            raise ResidentDaemonRepairApplyError(
                "repair apply target requires manual review",
                payload=_build_repair_apply_payload(
                    runtime_root=runtime_root,
                    requested_targets=requested_targets,
                    created_paths=tuple(created_paths),
                    result="requires_review",
                    applied=False,
                    failure_mode=f"{target.value}_review_required",
                    recovery_note="Review the conflicting artifact before repair apply.",
                    include_event_record=include_event_record,
                ),
            )
        path = target_paths[target]
        if not path.exists():
            path.mkdir(parents=True, exist_ok=False)
            created_paths.append(str(path))
    return _build_repair_apply_payload(
        runtime_root=runtime_root,
        requested_targets=requested_targets,
        created_paths=tuple(created_paths),
        result="applied" if created_paths else "no_action",
        applied=bool(created_paths),
        recovery_note="Only explicitly requested directory targets were created.",
        include_event_record=include_event_record,
    )
