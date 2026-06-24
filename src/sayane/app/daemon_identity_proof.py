"""Conservative resident daemon identity proof preview.

This module defines a proof-oriented identity contract without upgrading the
current evidence ceiling into actual verified daemon identity.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_process_control import (
    ResidentDaemonProcessStatusReport,
    build_daemon_status_report,
)
from sayane.app.daemon_proof_status import (
    ResidentDaemonProofDowngradeReason,
    ResidentDaemonProofStatus,
)

ResidentDaemonIdentityProofStatus = ResidentDaemonProofStatus


@dataclass(frozen=True)
class ResidentDaemonIdentityProof:
    """Proof-oriented identity payload without claiming verified identity."""

    runtime_root: Path
    status_report: ResidentDaemonProcessStatusReport
    identity: ResidentDaemonIdentity
    identity_status: ResidentDaemonIdentityProofStatus
    downgrade_reason: ResidentDaemonProofDowngradeReason
    evidence_ceiling: str
    observation_notes: tuple[str, ...]
    manual_review_required: bool
    proves_process_identity: bool = False
    proves_daemon_readiness: bool = False
    proves_api_readiness: bool = False
    probes_process: bool = True
    probes_api: bool = False
    mutates_filesystem: bool = False
    controls_process: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public identity-proof preview metadata."""
        return {
            "kind": "resident_daemon_identity_proof_preview",
            "preview_only": True,
            "runtime_root": str(self.runtime_root),
            "identity_status": self.identity_status.value,
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
            "identity": {
                "name": self.identity.name,
                "runtime_dir": str(self.identity.runtime_dir),
                "pid_path": str(self.identity.pid_path),
                "lock_path": str(self.identity.lock_path),
                "socket_path": str(self.identity.socket_path),
                "writes_files": self.identity.writes_files,
                "acquires_lock": self.identity.acquires_lock,
                "stale_lock_policy": self.identity.stale_lock_policy,
            },
            "status_report": self.status_report.public_metadata(),
        }


def build_identity_proof_from_status_report(
    status_report: ResidentDaemonProcessStatusReport,
) -> ResidentDaemonIdentityProof:
    """Build a conservative identity-proof preview from status evidence."""
    identity = ResidentDaemonIdentity(runtime_dir=status_report.runtime_root)
    notes: list[str] = [
        "identity proof requires stronger evidence than process existence",
        "current preview does not prove process ownership",
    ]

    if status_report.manual_review_required:
        if status_report.failure_mode is not None:
            notes.append(f"failure_mode:{status_report.failure_mode}")
        notes.append("manual review is required before stronger identity claims")
        return ResidentDaemonIdentityProof(
            runtime_root=status_report.runtime_root,
            status_report=status_report,
            identity=identity,
            identity_status=ResidentDaemonIdentityProofStatus.MANUAL_REVIEW_REQUIRED,
            downgrade_reason=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.PROCESS_STATUS_REQUIRES_MANUAL_REVIEW.value,
            observation_notes=tuple(notes),
            manual_review_required=True,
        )

    if not status_report.is_running_daemon:
        notes.append("no running daemon process is currently observed")
        return ResidentDaemonIdentityProof(
            runtime_root=status_report.runtime_root,
            status_report=status_report,
            identity=identity,
            identity_status=ResidentDaemonIdentityProofStatus.IDENTITY_NOT_RUNNING,
            downgrade_reason=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS,
            evidence_ceiling=ResidentDaemonProofDowngradeReason.NO_RUNNING_PROCESS.value,
            observation_notes=tuple(notes),
            manual_review_required=False,
        )

    if status_report.healthcheck_ok:
        notes.append("unauthenticated local health endpoint responded")
        notes.append("endpoint reachability is below the daemon identity proof threshold")
        downgrade_reason = ResidentDaemonProofDowngradeReason.UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY
    else:
        notes.append("running process observed through local process status")
        downgrade_reason = (
            ResidentDaemonProofDowngradeReason.PROCESS_EXISTENCE_WITHOUT_IDENTITY_PROOF
        )

    notes.append("runtime-root scoping is known, but daemon identity remains unverified")
    return ResidentDaemonIdentityProof(
        runtime_root=status_report.runtime_root,
        status_report=status_report,
        identity=identity,
        identity_status=ResidentDaemonIdentityProofStatus.IDENTITY_UNVERIFIED,
        downgrade_reason=downgrade_reason,
        evidence_ceiling=downgrade_reason.value,
        observation_notes=tuple(notes),
        manual_review_required=False,
    )


def build_identity_proof(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonIdentityProof:
    """Build a conservative resident daemon identity-proof preview."""
    return build_identity_proof_from_status_report(
        build_daemon_status_report(runtime_root, host=host, port=port),
    )
