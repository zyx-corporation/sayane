"""Schema-only resident daemon event records.

This module defines JSON-friendly event records for future resident daemon
preview and operation surfaces. It does not persist events, write files,
control processes, expose IPC, or integrate with OS services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from sayane.app.daemon_preflight import (
    ResidentDaemonPreflightReport,
    ResidentDaemonPreflightStatus,
)
from sayane.app.daemon_runtime_init import (
    ResidentDaemonRuntimeInitPlan,
    ResidentDaemonRuntimeInitStatus,
)


class ResidentDaemonEventCategory(StrEnum):
    """Resident daemon event categories."""

    PREVIEW = "preview"
    APPLY = "apply"
    PROCESS = "process"
    IPC = "ipc"
    SERVICE = "service"


class ResidentDaemonEventResult(StrEnum):
    """Conservative resident daemon event results."""

    PLANNED = "planned"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"
    REQUIRES_REVIEW = "requires_review"


@dataclass(frozen=True)
class ResidentDaemonEventRecord:
    """Schema-only event record for future resident daemon operations."""

    operation_id: str
    category: ResidentDaemonEventCategory
    surface: str
    result: ResidentDaemonEventResult = ResidentDaemonEventResult.PLANNED
    runtime_root: Path | None = None
    evidence: tuple[str, ...] = field(default_factory=tuple)
    consent: str = "not_required_for_preview"
    message: str | None = None
    mutates_filesystem: bool = False
    controls_process: bool = False
    exposes_ipc: bool = False
    integrates_os_service: bool = False

    def __post_init__(self) -> None:
        if not self.operation_id.strip():
            msg = "operation_id must not be empty"
            raise ValueError(msg)
        if not self.surface.strip():
            msg = "surface must not be empty"
            raise ValueError(msg)
        if self.category == ResidentDaemonEventCategory.PREVIEW:
            unsafe_flags = (
                self.mutates_filesystem,
                self.controls_process,
                self.exposes_ipc,
                self.integrates_os_service,
            )
            if any(unsafe_flags):
                msg = "preview event records must not set operation side-effect flags"
                raise ValueError(msg)

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive JSON-friendly event metadata."""
        return {
            "kind": "resident_daemon_event_record",
            "operation_id": self.operation_id,
            "category": self.category.value,
            "surface": self.surface,
            "result": self.result.value,
            "runtime_root": str(self.runtime_root) if self.runtime_root is not None else None,
            "evidence": list(self.evidence),
            "consent": self.consent,
            "message": self.message,
            "mutates_filesystem": self.mutates_filesystem,
            "controls_process": self.controls_process,
            "exposes_ipc": self.exposes_ipc,
            "integrates_os_service": self.integrates_os_service,
            "persisted": False,
        }


def _map_preflight_status_to_event_result(
    status: ResidentDaemonPreflightStatus,
) -> ResidentDaemonEventResult:
    if status is ResidentDaemonPreflightStatus.PASS:
        return ResidentDaemonEventResult.SUCCEEDED
    if status is ResidentDaemonPreflightStatus.REVIEW_REQUIRED:
        return ResidentDaemonEventResult.REQUIRES_REVIEW
    if status is ResidentDaemonPreflightStatus.BLOCKED:
        return ResidentDaemonEventResult.FAILED
    return ResidentDaemonEventResult.ABORTED


def build_preflight_event_record(
    report: ResidentDaemonPreflightReport,
    *,
    operation_id: str = "daemon-preflight",
    surface: str = "daemon-preflight",
    runtime_root: Path | None = None,
) -> ResidentDaemonEventRecord:
    """Build a schema-only preview event record from a preflight report."""
    attention_items = tuple(
        f"{item.key}:{item.status.value}"
        for item in report.items
        if item.status is not ResidentDaemonPreflightStatus.PASS
    )
    if not attention_items:
        attention_items = tuple(item.key for item in report.items)

    return ResidentDaemonEventRecord(
        operation_id=operation_id,
        category=ResidentDaemonEventCategory.PREVIEW,
        surface=surface,
        result=_map_preflight_status_to_event_result(report.status),
        runtime_root=runtime_root,
        evidence=attention_items,
        consent="not_required_for_preview",
        message=(
            "Schema-only implementation gate preflight preview: "
            f"status={report.status.value}, target_scope={report.target_scope}"
        ),
    )


def build_readiness_event_record(
    *,
    operation_id: str,
    runtime_root: Path,
    operation_class: str,
    readiness_status: str,
    api_readiness_status: str,
    evidence_ceiling: str,
    manual_review_required: bool,
) -> ResidentDaemonEventRecord:
    """Build a readiness diagnostic preview event record."""
    evidence = (
        f"operation_class:{operation_class}",
        f"readiness_status:{readiness_status}",
        f"api_readiness_status:{api_readiness_status}",
        f"evidence_ceiling:{evidence_ceiling}",
    )
    result = (
        ResidentDaemonEventResult.REQUIRES_REVIEW
        if manual_review_required
        else ResidentDaemonEventResult.PLANNED
    )
    message = (
        "Resident daemon readiness preview requires manual review."
        if manual_review_required
        else "Resident daemon readiness preview remains non-verifying."
    )
    return ResidentDaemonEventRecord(
        operation_id=operation_id,
        category=ResidentDaemonEventCategory.PREVIEW,
        surface="daemon-readiness-diagnostic",
        result=result,
        runtime_root=runtime_root,
        evidence=evidence,
        consent="not_required_for_preview",
        message=message,
    )


def build_runtime_init_event_record(
    plan: ResidentDaemonRuntimeInitPlan,
    *,
    applied: bool = False,
    attempted_apply: bool = False,
    created_paths: tuple[str, ...] = (),
    failure_mode: str | None = None,
    write_metadata: bool = False,
    confirm_operation_id: str | None = None,
    plan_fingerprint: str | None = None,
    confirm_plan_fingerprint: str | None = None,
    confirmation_matched: bool = False,
    fingerprint_matched: bool = False,
) -> ResidentDaemonEventRecord:
    """Build a runtime-init event record from preview/apply state."""
    manual_review_items = tuple(
        f"{item.path_role}:{item.status.value}"
        for item in plan.items
        if item.status is ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED
    )
    create_items = tuple(
        f"{item.path_role}:{item.status.value}"
        for item in plan.items
        if item.status is ResidentDaemonRuntimeInitStatus.CREATE
    )
    no_action_items = tuple(
        f"{item.path_role}:{item.status.value}"
        for item in plan.items
        if item.status is ResidentDaemonRuntimeInitStatus.NO_ACTION
    )
    consent_items = tuple(
        item
        for item in (
            f"write_metadata_requested:{str(write_metadata).lower()}",
            (
                f"confirm_operation_id:{confirm_operation_id}"
                if confirm_operation_id is not None
                else None
            ),
            f"plan_fingerprint:{plan_fingerprint}" if plan_fingerprint is not None else None,
            (
                f"confirm_plan_fingerprint:{confirm_plan_fingerprint}"
                if confirm_plan_fingerprint is not None
                else None
            ),
            f"confirmation_matched:{str(confirmation_matched).lower()}",
            f"fingerprint_matched:{str(fingerprint_matched).lower()}",
        )
        if item is not None
    )

    if manual_review_items:
        result = ResidentDaemonEventResult.REQUIRES_REVIEW
        evidence = manual_review_items + consent_items
        message = "Runtime init requires manual review before apply."
    elif applied:
        result = ResidentDaemonEventResult.SUCCEEDED
        evidence = (created_paths or no_action_items or create_items) + consent_items
        message = f"Runtime init apply completed under {plan.runtime_root}."
    elif attempted_apply:
        result = ResidentDaemonEventResult.ABORTED
        evidence = (create_items or no_action_items) + consent_items
        message = f"Runtime init apply aborted for {plan.runtime_root}."
    else:
        result = ResidentDaemonEventResult.PLANNED
        evidence = (create_items or no_action_items) + consent_items
        message = f"Runtime init preview prepared for {plan.runtime_root}."

    if failure_mode and not manual_review_items:
        result = ResidentDaemonEventResult.FAILED
        evidence = evidence + (f"failure_mode:{failure_mode}",)
        message = f"Runtime init apply failed: {failure_mode}"
    elif failure_mode:
        evidence = evidence + (f"failure_mode:{failure_mode}",)

    return ResidentDaemonEventRecord(
        operation_id=plan.operation_id,
        category=(
            ResidentDaemonEventCategory.APPLY
            if applied or attempted_apply
            else ResidentDaemonEventCategory.PREVIEW
        ),
        surface=plan.creator_surface,
        result=result,
        runtime_root=plan.runtime_root,
        evidence=evidence,
        consent=(
            "operator_apply_and_confirm_required"
            if write_metadata
            else ("required" if applied or attempted_apply else "operator_apply_required")
        ),
        message=message,
        mutates_filesystem=applied,
    )


def build_process_control_event_record(
    *,
    operation_id: str,
    operation: str,
    runtime_root: Path,
    result: str,
    state_before: str,
    state_after: str,
    host: str,
    port: int,
    pid: int | None = None,
    failure_mode: str | None = None,
    manual_review_required: bool = False,
    applied: bool = False,
) -> ResidentDaemonEventRecord:
    """Build a process-control event record from a control receipt."""
    evidence = [
        f"operation:{operation}",
        f"state_before:{state_before}",
        f"state_after:{state_after}",
        f"host:{host}",
        f"port:{port}",
        f"applied:{str(applied).lower()}",
    ]
    if pid is not None:
        evidence.append(f"pid:{pid}")
    if failure_mode is not None:
        evidence.append(f"failure_mode:{failure_mode}")

    if manual_review_required:
        event_result = ResidentDaemonEventResult.REQUIRES_REVIEW
        message = f"Resident daemon {operation} requires manual review."
    elif result in {"started", "stopped", "restarted"}:
        event_result = ResidentDaemonEventResult.SUCCEEDED
        message = f"Resident daemon {operation} completed."
    elif result == "no_action":
        event_result = ResidentDaemonEventResult.ABORTED
        message = f"Resident daemon {operation} had no target process."
    elif result == "aborted":
        event_result = ResidentDaemonEventResult.ABORTED
        message = f"Resident daemon {operation} was aborted."
    else:
        event_result = ResidentDaemonEventResult.FAILED
        message = f"Resident daemon {operation} failed."

    exposes_ipc = operation in {"start", "restart"} and applied
    mutates_filesystem = operation in {"start", "stop", "restart"} and applied
    return ResidentDaemonEventRecord(
        operation_id=operation_id,
        category=ResidentDaemonEventCategory.PROCESS,
        surface=f"daemon-{operation}",
        result=event_result,
        runtime_root=runtime_root,
        evidence=tuple(evidence),
        consent="required",
        message=message,
        mutates_filesystem=mutates_filesystem,
        controls_process=True,
        exposes_ipc=exposes_ipc,
    )


def build_cleanup_apply_event_record(
    *,
    operation_id: str,
    runtime_root: Path,
    requested_targets: tuple[str, ...],
    removed_paths: tuple[str, ...],
    result: str,
    failure_mode: str | None = None,
    applied: bool = False,
) -> ResidentDaemonEventRecord:
    """Build a cleanup-apply event record."""
    evidence = [*(f"requested_target:{target}" for target in requested_targets)]
    evidence.extend(f"removed_path:{path}" for path in removed_paths)
    if failure_mode is not None:
        evidence.append(f"failure_mode:{failure_mode}")

    if result == "applied":
        event_result = ResidentDaemonEventResult.SUCCEEDED
        message = "Resident daemon cleanup apply completed."
    elif result == "requires_review":
        event_result = ResidentDaemonEventResult.REQUIRES_REVIEW
        message = "Resident daemon cleanup apply requires manual review."
    elif result in {"aborted", "no_action"}:
        event_result = ResidentDaemonEventResult.ABORTED
        message = "Resident daemon cleanup apply had no effect."
    else:
        event_result = ResidentDaemonEventResult.FAILED
        message = "Resident daemon cleanup apply failed."

    return ResidentDaemonEventRecord(
        operation_id=operation_id,
        category=ResidentDaemonEventCategory.APPLY,
        surface="daemon-cleanup-apply",
        result=event_result,
        runtime_root=runtime_root,
        evidence=tuple(evidence),
        consent="required",
        message=message,
        mutates_filesystem=applied,
    )


def build_repair_apply_event_record(
    *,
    operation_id: str,
    runtime_root: Path,
    requested_targets: tuple[str, ...],
    created_paths: tuple[str, ...],
    result: str,
    failure_mode: str | None = None,
    applied: bool = False,
) -> ResidentDaemonEventRecord:
    """Build a repair-apply event record."""
    evidence = [*(f"requested_target:{target}" for target in requested_targets)]
    evidence.extend(f"created_path:{path}" for path in created_paths)
    if failure_mode is not None:
        evidence.append(f"failure_mode:{failure_mode}")

    if result == "applied":
        event_result = ResidentDaemonEventResult.SUCCEEDED
        message = "Resident daemon repair apply completed."
    elif result == "requires_review":
        event_result = ResidentDaemonEventResult.REQUIRES_REVIEW
        message = "Resident daemon repair apply requires manual review."
    elif result in {"aborted", "no_action"}:
        event_result = ResidentDaemonEventResult.ABORTED
        message = "Resident daemon repair apply had no effect."
    else:
        event_result = ResidentDaemonEventResult.FAILED
        message = "Resident daemon repair apply failed."

    return ResidentDaemonEventRecord(
        operation_id=operation_id,
        category=ResidentDaemonEventCategory.APPLY,
        surface="daemon-repair-apply",
        result=event_result,
        runtime_root=runtime_root,
        evidence=tuple(evidence),
        consent="required",
        message=message,
        mutates_filesystem=applied,
    )
