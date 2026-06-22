"""Conservative resident daemon readiness proof preview.

This module defines a proof-oriented readiness contract without upgrading the
current evidence ceiling into verified daemon or API readiness.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sayane.app.daemon_process_control import (
    ResidentDaemonProcessStatusReport,
    build_daemon_status_report,
)
from sayane.app.daemon_proof_status import (
    ResidentDaemonProofDowngradeReason,
    ResidentDaemonProofStatus,
)

ResidentDaemonReadinessProofStatus = ResidentDaemonProofStatus


@dataclass(frozen=True)
class ResidentDaemonReadinessProof:
    """Proof-oriented readiness payload without claiming verified readiness."""

    runtime_root: Path
    operation_class: str
    status_report: ResidentDaemonProcessStatusReport
    readiness_status: ResidentDaemonReadinessProofStatus
    downgrade_reason: ResidentDaemonProofDowngradeReason
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
        """Return public readiness-proof preview metadata."""
        return {
            "kind": "resident_daemon_readiness_proof_preview",
            "preview_only": True,
            "runtime_root": str(self.runtime_root),
            "operation_class": self.operation_class,
            "readiness_status": self.readiness_status.value,
            "downgrade_reason": self.downgrade_reason.value,
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


def build_readiness_proof_from_status_report(
    status_report: ResidentDaemonProcessStatusReport,
    *,
    operation_class: str = "bridge_health",
) -> ResidentDaemonReadinessProof:
    """Build a conservative readiness-proof preview from status evidence."""
    notes: list[str] = [f"operation_class:{operation_class}"]
    if status_report.manual_review_required:
        if status_report.failure_mode is not None:
            notes.append(f"failure_mode:{status_report.failure_mode}")
        notes.append("manual review is required before stronger readiness claims")
        return ResidentDaemonReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            readiness_status=ResidentDaemonReadinessProofStatus.MANUAL_REVIEW_REQUIRED,
            downgrade_reason=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW.value,
            observation_notes=tuple(notes),
            manual_review_required=True,
        )

    if not status_report.is_running_daemon:
        notes.append("no running daemon process is currently observed")
        return ResidentDaemonReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            readiness_status=ResidentDaemonReadinessProofStatus.READINESS_NOT_READY,
            downgrade_reason=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS.value,
            observation_notes=tuple(notes),
            manual_review_required=False,
        )

    if status_report.healthcheck_ok:
        notes.append("unauthenticated local health endpoint responded")
        notes.append("endpoint reachability does not prove authentication or authorization")
        notes.append("current proof preview does not verify operation-class readiness")
        return ResidentDaemonReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            readiness_status=ResidentDaemonReadinessProofStatus.READINESS_UNVERIFIED,
            downgrade_reason=ResidentDaemonProofDowngradeReason.UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY.value,
            observation_notes=tuple(notes),
            manual_review_required=False,
        )

    notes.append("running process observed without successful health response")
    notes.append("current proof preview cannot verify ready-for-operation state")
    return ResidentDaemonReadinessProof(
        runtime_root=status_report.runtime_root,
        operation_class=operation_class,
        status_report=status_report,
        readiness_status=ResidentDaemonReadinessProofStatus.READINESS_DEGRADED,
        downgrade_reason=ResidentDaemonProofDowngradeReason.PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_READINESS,
        evidence_ceiling=ResidentDaemonProofDowngradeReason.PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_READINESS.value,
        observation_notes=tuple(notes),
        manual_review_required=False,
    )


def build_readiness_proof(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    operation_class: str = "bridge_health",
) -> ResidentDaemonReadinessProof:
    """Build a conservative resident daemon readiness-proof preview."""
    return build_readiness_proof_from_status_report(
        build_daemon_status_report(runtime_root, host=host, port=port),
        operation_class=operation_class,
    )
