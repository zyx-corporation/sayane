"""Conservative resident daemon readiness diagnostic preview.

This module uses the current local-only process status report and unauthenticated
health endpoint reachability as weak observations only. It does not prove daemon
readiness or API readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from sayane.app.daemon_process_control import (
    ResidentDaemonProcessStatusReport,
    build_daemon_status_report,
)


class ResidentDaemonReadinessStatus(StrEnum):
    """Conservative daemon readiness status."""

    READINESS_UNVERIFIED = "readiness_unverified"
    READINESS_NOT_READY = "readiness_not_ready"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class ResidentDaemonApiReadinessStatus(StrEnum):
    """Conservative local API readiness status."""

    API_READINESS_UNVERIFIED = "api_readiness_unverified"
    API_UNREACHABLE = "api_unreachable"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class ResidentDaemonReadinessDiagnostic:
    """Read-only resident daemon readiness and API readiness preview."""

    runtime_root: Path
    operation_class: str
    status_report: ResidentDaemonProcessStatusReport
    readiness_status: ResidentDaemonReadinessStatus
    api_readiness_status: ResidentDaemonApiReadinessStatus
    evidence_ceiling: str
    observation_notes: tuple[str, ...]
    manual_review_required: bool
    proves_process_identity: bool = False
    proves_daemon_readiness: bool = False
    proves_api_readiness: bool = False
    probes_process: bool = True
    probes_api: bool = True
    mutates_filesystem: bool = False
    controls_process: bool = False

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_readiness_diagnostic_preview",
            "preview_only": True,
            "runtime_root": str(self.runtime_root),
            "operation_class": self.operation_class,
            "readiness_status": self.readiness_status.value,
            "api_readiness_status": self.api_readiness_status.value,
            "evidence_ceiling": self.evidence_ceiling,
            "observation_notes": list(self.observation_notes),
            "manual_review_required": self.manual_review_required,
            "proves_process_identity": self.proves_process_identity,
            "proves_daemon_readiness": self.proves_daemon_readiness,
            "proves_api_readiness": self.proves_api_readiness,
            "probes_process": self.probes_process,
            "probes_api": self.probes_api,
            "mutates_filesystem": self.mutates_filesystem,
            "controls_process": self.controls_process,
            "status_report": self.status_report.public_metadata(),
        }


def build_readiness_diagnostic_from_status_report(
    status_report: ResidentDaemonProcessStatusReport,
    *,
    operation_class: str = "bridge_health",
) -> ResidentDaemonReadinessDiagnostic:
    """Build a conservative readiness diagnostic from the current status report."""
    notes: list[str] = [f"operation_class:{operation_class}"]
    if status_report.manual_review_required:
        if status_report.failure_mode is not None:
            notes.append(f"failure_mode:{status_report.failure_mode}")
        notes.append("manual review is required before stronger readiness claims")
        return ResidentDaemonReadinessDiagnostic(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            readiness_status=ResidentDaemonReadinessStatus.MANUAL_REVIEW_REQUIRED,
            api_readiness_status=ResidentDaemonApiReadinessStatus.MANUAL_REVIEW_REQUIRED,
            evidence_ceiling="process_status_requires_manual_review",
            observation_notes=tuple(notes),
            manual_review_required=True,
        )

    if not status_report.is_running_daemon:
        notes.append("no running daemon process is currently observed")
        return ResidentDaemonReadinessDiagnostic(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            readiness_status=ResidentDaemonReadinessStatus.READINESS_NOT_READY,
            api_readiness_status=ResidentDaemonApiReadinessStatus.API_UNREACHABLE,
            evidence_ceiling="no_running_process",
            observation_notes=tuple(notes),
            manual_review_required=False,
        )

    if status_report.healthcheck_ok:
        notes.append("unauthenticated local health endpoint responded")
        notes.append("endpoint reachability does not prove authentication or authorization")
        evidence_ceiling = "unauthenticated_health_endpoint_only"
        api_status = ResidentDaemonApiReadinessStatus.API_READINESS_UNVERIFIED
    else:
        notes.append("running process observed without successful health response")
        evidence_ceiling = "process_existence_without_authenticated_readiness"
        api_status = ResidentDaemonApiReadinessStatus.API_UNREACHABLE

    notes.append("current preview does not prove process identity")
    notes.append("current preview does not prove daemon readiness")
    return ResidentDaemonReadinessDiagnostic(
        runtime_root=status_report.runtime_root,
        operation_class=operation_class,
        status_report=status_report,
        readiness_status=ResidentDaemonReadinessStatus.READINESS_UNVERIFIED,
        api_readiness_status=api_status,
        evidence_ceiling=evidence_ceiling,
        observation_notes=tuple(notes),
        manual_review_required=False,
    )


def build_readiness_diagnostic(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    operation_class: str = "bridge_health",
) -> ResidentDaemonReadinessDiagnostic:
    """Build a conservative readiness diagnostic preview."""
    return build_readiness_diagnostic_from_status_report(
        build_daemon_status_report(runtime_root, host=host, port=port),
        operation_class=operation_class,
    )
