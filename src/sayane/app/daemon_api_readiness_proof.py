"""Conservative resident daemon API readiness proof preview.

This module defines a proof-oriented API-readiness contract without upgrading
the current evidence ceiling into verified authenticated API usability.
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

ResidentDaemonApiReadinessProofStatus = ResidentDaemonProofStatus


@dataclass(frozen=True)
class ResidentDaemonApiReadinessProof:
    """Proof-oriented API-readiness payload without claiming verified usability."""

    runtime_root: Path
    operation_class: str
    status_report: ResidentDaemonProcessStatusReport
    api_readiness_status: ResidentDaemonApiReadinessProofStatus
    downgrade_reason: ResidentDaemonProofDowngradeReason
    evidence_ceiling: str
    observation_notes: tuple[str, ...]
    observed_api_reachable: bool
    observed_authenticated: bool
    observed_authorized: bool
    observed_protocol_compatible: bool | None
    manual_review_required: bool
    proves_process_identity: bool = False
    proves_daemon_readiness: bool = False
    proves_api_readiness: bool = False
    probes_process: bool = True
    probes_api: bool = True
    mutates_filesystem: bool = False
    controls_process: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public API-readiness proof preview metadata."""
        return {
            "kind": "resident_daemon_api_readiness_proof_preview",
            "preview_only": True,
            "runtime_root": str(self.runtime_root),
            "operation_class": self.operation_class,
            "api_readiness_status": self.api_readiness_status.value,
            "downgrade_reason": self.downgrade_reason.value,
            "evidence_ceiling": self.evidence_ceiling,
            "observation_notes": list(self.observation_notes),
            "observed_api_reachable": self.observed_api_reachable,
            "observed_authenticated": self.observed_authenticated,
            "observed_authorized": self.observed_authorized,
            "observed_protocol_compatible": self.observed_protocol_compatible,
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


def build_api_readiness_proof_from_status_report(
    status_report: ResidentDaemonProcessStatusReport,
    *,
    operation_class: str = "bridge_health",
) -> ResidentDaemonApiReadinessProof:
    """Build a conservative API-readiness proof preview from status evidence."""
    notes: list[str] = [f"operation_class:{operation_class}"]
    if status_report.manual_review_required:
        if status_report.failure_mode is not None:
            notes.append(f"failure_mode:{status_report.failure_mode}")
        notes.append("manual review is required before stronger API-readiness claims")
        return ResidentDaemonApiReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            api_readiness_status=ResidentDaemonApiReadinessProofStatus.MANUAL_REVIEW_REQUIRED,
            downgrade_reason=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW.value,
            observation_notes=tuple(notes),
            observed_api_reachable=False,
            observed_authenticated=False,
            observed_authorized=False,
            observed_protocol_compatible=None,
            manual_review_required=True,
        )

    if not status_report.is_running_daemon:
        notes.append("no running daemon process is currently observed")
        return ResidentDaemonApiReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            api_readiness_status=ResidentDaemonApiReadinessProofStatus.API_UNREACHABLE,
            downgrade_reason=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS.value,
            observation_notes=tuple(notes),
            observed_api_reachable=False,
            observed_authenticated=False,
            observed_authorized=False,
            observed_protocol_compatible=None,
            manual_review_required=False,
        )

    if status_report.healthcheck_ok:
        notes.append("unauthenticated local health endpoint responded")
        notes.append("endpoint reachability is below authenticated API readiness proof")
        notes.append("authorization and protocol compatibility remain unverified")
        return ResidentDaemonApiReadinessProof(
            runtime_root=status_report.runtime_root,
            operation_class=operation_class,
            status_report=status_report,
            api_readiness_status=ResidentDaemonApiReadinessProofStatus.API_UNAUTHENTICATED,
            downgrade_reason=ResidentDaemonProofDowngradeReason.UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY.value,
            observation_notes=tuple(notes),
            observed_api_reachable=True,
            observed_authenticated=False,
            observed_authorized=False,
            observed_protocol_compatible=None,
            manual_review_required=False,
        )

    notes.append("running process observed without successful health response")
    notes.append("current proof preview cannot verify API reachability for this operation class")
    return ResidentDaemonApiReadinessProof(
        runtime_root=status_report.runtime_root,
        operation_class=operation_class,
        status_report=status_report,
        api_readiness_status=ResidentDaemonApiReadinessProofStatus.API_UNREACHABLE,
        downgrade_reason=ResidentDaemonProofDowngradeReason.PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_API_REACHABILITY,
        evidence_ceiling=ResidentDaemonProofDowngradeReason.PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_API_REACHABILITY.value,
        observation_notes=tuple(notes),
        observed_api_reachable=False,
        observed_authenticated=False,
        observed_authorized=False,
        observed_protocol_compatible=None,
        manual_review_required=False,
    )


def build_api_readiness_proof(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    operation_class: str = "bridge_health",
) -> ResidentDaemonApiReadinessProof:
    """Build a conservative resident daemon API-readiness proof preview."""
    return build_api_readiness_proof_from_status_report(
        build_daemon_status_report(runtime_root, host=host, port=port),
        operation_class=operation_class,
    )
