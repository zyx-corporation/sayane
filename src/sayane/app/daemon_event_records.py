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
