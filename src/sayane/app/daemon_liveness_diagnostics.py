"""Read-only resident daemon liveness diagnostic preview.

This module deliberately does not probe or control operating-system processes.
It consumes the existing PID file parse diagnostic and reports the current
liveness evidence ceiling.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_pid_diagnostics import (
    ResidentDaemonPidFileDiagnostic,
    ResidentDaemonPidParseStatus,
    build_pid_file_diagnostic,
)


class ResidentDaemonLivenessStatus(StrEnum):
    """Conservative resident daemon liveness diagnostic status."""

    PID_MISSING_LIVENESS_UNVERIFIED = "pid_missing_liveness_unverified"
    PID_UNREADABLE_LIVENESS_UNVERIFIED = "pid_unreadable_liveness_unverified"
    PID_EMPTY_LIVENESS_UNVERIFIED = "pid_empty_liveness_unverified"
    PID_INVALID_LIVENESS_UNVERIFIED = "pid_invalid_liveness_unverified"
    PID_PARSED_PROCESS_UNVERIFIED = "pid_parsed_process_unverified"


@dataclass(frozen=True)
class ResidentDaemonLivenessDiagnostic:
    """Read-only resident daemon liveness diagnostic preview."""

    pid_diagnostic: ResidentDaemonPidFileDiagnostic
    status: ResidentDaemonLivenessStatus
    evidence_ceiling: str
    manual_review_required: bool
    proves_liveness: bool = False
    probes_process: bool = False
    controls_process: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public liveness diagnostic preview metadata."""
        return {
            "kind": "resident_daemon_liveness_diagnostic_preview",
            "preview_only": True,
            "status": self.status.value,
            "evidence_ceiling": self.evidence_ceiling,
            "manual_review_required": self.manual_review_required,
            "proves_liveness": self.proves_liveness,
            "probes_process": self.probes_process,
            "controls_process": self.controls_process,
            "mutates_filesystem": self.mutates_filesystem,
            "pid_file": self.pid_diagnostic.public_metadata(),
        }


def _map_pid_status_to_liveness_status(
    status: ResidentDaemonPidParseStatus,
) -> ResidentDaemonLivenessStatus:
    if status == ResidentDaemonPidParseStatus.MISSING:
        return ResidentDaemonLivenessStatus.PID_MISSING_LIVENESS_UNVERIFIED
    if status == ResidentDaemonPidParseStatus.UNREADABLE:
        return ResidentDaemonLivenessStatus.PID_UNREADABLE_LIVENESS_UNVERIFIED
    if status == ResidentDaemonPidParseStatus.EMPTY:
        return ResidentDaemonLivenessStatus.PID_EMPTY_LIVENESS_UNVERIFIED
    if status == ResidentDaemonPidParseStatus.INVALID:
        return ResidentDaemonLivenessStatus.PID_INVALID_LIVENESS_UNVERIFIED
    if status == ResidentDaemonPidParseStatus.PARSED:
        return ResidentDaemonLivenessStatus.PID_PARSED_PROCESS_UNVERIFIED
    raise ValueError(f"Unsupported PID diagnostic status: {status}")


def _evidence_ceiling_for_liveness_status(status: ResidentDaemonLivenessStatus) -> str:
    if status == ResidentDaemonLivenessStatus.PID_PARSED_PROCESS_UNVERIFIED:
        return "pid_file_parsed_only"
    return "pid_file_diagnostic_only"


def build_liveness_diagnostic_from_pid_file_diagnostic(
    pid_diagnostic: ResidentDaemonPidFileDiagnostic,
) -> ResidentDaemonLivenessDiagnostic:
    """Build a liveness diagnostic preview from a PID file diagnostic."""
    status = _map_pid_status_to_liveness_status(pid_diagnostic.status)
    return ResidentDaemonLivenessDiagnostic(
        pid_diagnostic=pid_diagnostic,
        status=status,
        evidence_ceiling=_evidence_ceiling_for_liveness_status(status),
        manual_review_required=pid_diagnostic.manual_review_required,
    )


def build_liveness_diagnostic(
    identity: ResidentDaemonIdentity,
) -> ResidentDaemonLivenessDiagnostic:
    """Build a read-only resident daemon liveness diagnostic preview."""
    return build_liveness_diagnostic_from_pid_file_diagnostic(
        build_pid_file_diagnostic(identity),
    )
