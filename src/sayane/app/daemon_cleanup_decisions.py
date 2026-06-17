"""Non-mutating resident daemon cleanup decision model.

This module converts stale artifact diagnostics into conservative cleanup
recommendations. It does not delete, repair, create, or mutate filesystem
artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from sayane.app.daemon_stale_artifacts import (
    ResidentDaemonArtifactDiagnostic,
    ResidentDaemonArtifactStatus,
    ResidentDaemonStaleArtifactReport,
)


class ResidentDaemonCleanupRecommendation(StrEnum):
    """Conservative cleanup recommendations."""

    NO_ACTION = "no_action"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    UNSAFE_TO_DELETE = "unsafe_to_delete"
    FUTURE_CLEANUP_CANDIDATE = "future_cleanup_candidate"


@dataclass(frozen=True)
class ResidentDaemonCleanupDecision:
    """Non-mutating decision for one daemon runtime artifact."""

    artifact_kind: str
    path: str
    diagnostic_status: str
    recommendation: ResidentDaemonCleanupRecommendation
    reason: str
    manual_review_required: bool
    safe_to_delete: bool = False
    deletes_artifact: bool = False
    repairs_artifact: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public cleanup decision metadata."""
        return {
            "artifact_kind": self.artifact_kind,
            "path": self.path,
            "diagnostic_status": self.diagnostic_status,
            "recommendation": self.recommendation.value,
            "reason": self.reason,
            "manual_review_required": self.manual_review_required,
            "safe_to_delete": self.safe_to_delete,
            "deletes_artifact": self.deletes_artifact,
            "repairs_artifact": self.repairs_artifact,
            "mutates_filesystem": self.mutates_filesystem,
        }


@dataclass(frozen=True)
class ResidentDaemonCleanupDecisionReport:
    """Non-mutating cleanup decision report."""

    runtime_root: str
    decisions: tuple[ResidentDaemonCleanupDecision, ...]
    decision_policy: str = "manual_review_required"
    preview_only: bool = True
    deletes_artifacts: bool = False
    repairs_artifacts: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public cleanup report metadata."""
        return {
            "kind": "resident_daemon_cleanup_decision_preview",
            "preview_only": self.preview_only,
            "runtime_root": self.runtime_root,
            "decision_policy": self.decision_policy,
            "deletes_artifacts": self.deletes_artifacts,
            "repairs_artifacts": self.repairs_artifacts,
            "mutates_filesystem": self.mutates_filesystem,
            "manual_review_required": any(
                decision.manual_review_required for decision in self.decisions
            ),
            "decisions": [decision.public_metadata() for decision in self.decisions],
        }


def _decision_for_missing(
    diagnostic: ResidentDaemonArtifactDiagnostic,
) -> ResidentDaemonCleanupDecision:
    return ResidentDaemonCleanupDecision(
        artifact_kind=diagnostic.kind.value,
        path=str(diagnostic.path),
        diagnostic_status=diagnostic.status.value,
        recommendation=ResidentDaemonCleanupRecommendation.NO_ACTION,
        reason="artifact is missing; no cleanup is needed",
        manual_review_required=False,
    )


def _decision_for_present(
    diagnostic: ResidentDaemonArtifactDiagnostic,
) -> ResidentDaemonCleanupDecision:
    return ResidentDaemonCleanupDecision(
        artifact_kind=diagnostic.kind.value,
        path=str(diagnostic.path),
        diagnostic_status=diagnostic.status.value,
        recommendation=ResidentDaemonCleanupRecommendation.MANUAL_REVIEW_REQUIRED,
        reason="artifact is present; ownership and liveness are not proven by preview diagnostics",
        manual_review_required=True,
    )


def _decision_for_type_mismatch(
    diagnostic: ResidentDaemonArtifactDiagnostic,
) -> ResidentDaemonCleanupDecision:
    return ResidentDaemonCleanupDecision(
        artifact_kind=diagnostic.kind.value,
        path=str(diagnostic.path),
        diagnostic_status=diagnostic.status.value,
        recommendation=ResidentDaemonCleanupRecommendation.UNSAFE_TO_DELETE,
        reason="artifact type mismatch requires manual review before any cleanup",
        manual_review_required=True,
    )


def build_cleanup_decision(
    diagnostic: ResidentDaemonArtifactDiagnostic,
) -> ResidentDaemonCleanupDecision:
    """Build a conservative non-mutating cleanup decision for one diagnostic."""
    if diagnostic.status is ResidentDaemonArtifactStatus.MISSING:
        return _decision_for_missing(diagnostic)
    if diagnostic.status is ResidentDaemonArtifactStatus.PRESENT_REVIEW_REQUIRED:
        return _decision_for_present(diagnostic)
    if diagnostic.status is ResidentDaemonArtifactStatus.TYPE_MISMATCH_REVIEW_REQUIRED:
        return _decision_for_type_mismatch(diagnostic)
    return ResidentDaemonCleanupDecision(
        artifact_kind=diagnostic.kind.value,
        path=str(diagnostic.path),
        diagnostic_status=diagnostic.status.value,
        recommendation=ResidentDaemonCleanupRecommendation.MANUAL_REVIEW_REQUIRED,
        reason="unknown diagnostic status requires manual review",
        manual_review_required=True,
    )


def build_cleanup_decision_report(
    report: ResidentDaemonStaleArtifactReport,
) -> ResidentDaemonCleanupDecisionReport:
    """Build a non-mutating cleanup decision report from stale artifact diagnostics."""
    return ResidentDaemonCleanupDecisionReport(
        runtime_root=str(report.layout.runtime_root),
        decisions=tuple(build_cleanup_decision(diagnostic) for diagnostic in report.diagnostics),
    )
