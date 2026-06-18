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


def build_runtime_init_event_record(
    plan: ResidentDaemonRuntimeInitPlan,
    *,
    applied: bool = False,
    created_paths: tuple[str, ...] = (),
    failure_mode: str | None = None,
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

    if manual_review_items:
        result = ResidentDaemonEventResult.REQUIRES_REVIEW
        evidence = manual_review_items
        message = "Runtime init requires manual review before apply."
    elif applied:
        result = ResidentDaemonEventResult.SUCCEEDED
        evidence = created_paths or no_action_items or create_items
        message = f"Runtime init apply completed under {plan.runtime_root}."
    else:
        result = ResidentDaemonEventResult.PLANNED
        evidence = create_items or no_action_items
        message = f"Runtime init preview prepared for {plan.runtime_root}."

    if failure_mode:
        result = ResidentDaemonEventResult.FAILED
        evidence = evidence + (f"failure_mode:{failure_mode}",)
        message = f"Runtime init apply failed: {failure_mode}"

    return ResidentDaemonEventRecord(
        operation_id=plan.operation_id,
        category=(
            ResidentDaemonEventCategory.APPLY if applied else ResidentDaemonEventCategory.PREVIEW
        ),
        surface=plan.creator_surface,
        result=result,
        runtime_root=plan.runtime_root,
        evidence=evidence,
        consent="required" if applied else "operator_apply_required",
        message=message,
        mutates_filesystem=applied,
    )
