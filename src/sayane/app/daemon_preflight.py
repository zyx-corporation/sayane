"""Schema-only resident daemon implementation preflight checklist.

This module defines a JSON-friendly preflight report for future resident daemon
implementation planning. It does not inspect processes, mutate files, expose
IPC, or integrate with OS services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResidentDaemonPreflightStatus(StrEnum):
    """Conservative preflight item status."""

    PASS = "pass"
    REVIEW_REQUIRED = "review_required"
    BLOCKED = "blocked"
    NOT_APPLICABLE = "not_applicable"


class ResidentDaemonPreflightCategory(StrEnum):
    """Resident daemon preflight category."""

    EVIDENCE = "evidence"
    MUTATION = "mutation"
    OPERATOR = "operator"
    IPC = "ipc"
    PROCESS = "process"
    SERVICE = "service"
    RELEASE = "release"


@dataclass(frozen=True)
class ResidentDaemonPreflightItem:
    """One preflight checklist item."""

    key: str
    category: ResidentDaemonPreflightCategory
    status: ResidentDaemonPreflightStatus
    summary: str
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.key.strip():
            msg = "preflight item key must not be empty"
            raise ValueError(msg)
        if not self.summary.strip():
            msg = "preflight item summary must not be empty"
            raise ValueError(msg)

    def public_metadata(self) -> dict[str, Any]:
        """Return JSON-friendly preflight item metadata."""
        return {
            "key": self.key,
            "category": self.category.value,
            "status": self.status.value,
            "summary": self.summary,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ResidentDaemonPreflightReport:
    """Schema-only implementation preflight report."""

    items: tuple[ResidentDaemonPreflightItem, ...]
    target_scope: str = "resident_daemon_implementation_gate"
    mutates_filesystem: bool = False
    probes_process: bool = False
    controls_process: bool = False
    exposes_ipc: bool = False
    integrates_os_service: bool = False

    @property
    def status(self) -> ResidentDaemonPreflightStatus:
        """Return aggregate conservative preflight status."""
        item_statuses = {item.status for item in self.items}
        if ResidentDaemonPreflightStatus.BLOCKED in item_statuses:
            return ResidentDaemonPreflightStatus.BLOCKED
        if ResidentDaemonPreflightStatus.REVIEW_REQUIRED in item_statuses:
            return ResidentDaemonPreflightStatus.REVIEW_REQUIRED
        return ResidentDaemonPreflightStatus.PASS

    def public_metadata(self) -> dict[str, Any]:
        """Return JSON-friendly preflight report metadata."""
        return {
            "kind": "resident_daemon_preflight_report",
            "target_scope": self.target_scope,
            "status": self.status.value,
            "items": [item.public_metadata() for item in self.items],
            "mutates_filesystem": self.mutates_filesystem,
            "probes_process": self.probes_process,
            "controls_process": self.controls_process,
            "exposes_ipc": self.exposes_ipc,
            "integrates_os_service": self.integrates_os_service,
        }


def build_implementation_gate_preflight_report() -> ResidentDaemonPreflightReport:
    """Build the default schema-only implementation gate preflight report."""
    return ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="evidence_ladder_documented",
                category=ResidentDaemonPreflightCategory.EVIDENCE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="Evidence ladder is documented from PID parsing through API readiness.",
                evidence=("docs/architecture/resident-daemon-implementation-readiness-gate.md",),
            ),
            ResidentDaemonPreflightItem(
                key="mutation_boundary_documented",
                category=ResidentDaemonPreflightCategory.MUTATION,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="Mutation authorization and cleanup/repair boundaries are documented.",
                evidence=("docs/architecture/resident-daemon-mutation-authorization-policy.md",),
            ),
            ResidentDaemonPreflightItem(
                key="operator_consent_documented",
                category=ResidentDaemonPreflightCategory.OPERATOR,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="Operator consent and preview/apply conventions are documented.",
                evidence=(
                    "docs/architecture/resident-daemon-operator-runbook-and-consent-policy.md",
                ),
            ),
            ResidentDaemonPreflightItem(
                key="ipc_authentication_future_work",
                category=ResidentDaemonPreflightCategory.IPC,
                status=ResidentDaemonPreflightStatus.REVIEW_REQUIRED,
                summary="Local IPC authentication is policy-only; implementation remains future work.",
                evidence=("docs/architecture/resident-daemon-local-ipc-authentication-policy.md",),
            ),
            ResidentDaemonPreflightItem(
                key="process_control_future_work",
                category=ResidentDaemonPreflightCategory.PROCESS,
                status=ResidentDaemonPreflightStatus.REVIEW_REQUIRED,
                summary="Process control policy exists, but process behavior remains future work.",
                evidence=("docs/architecture/resident-daemon-process-control-policy.md",),
            ),
            ResidentDaemonPreflightItem(
                key="os_service_integration_deferred",
                category=ResidentDaemonPreflightCategory.SERVICE,
                status=ResidentDaemonPreflightStatus.NOT_APPLICABLE,
                summary="OS service integration is deferred for the minimal first implementation.",
                evidence=("docs/architecture/resident-daemon-os-service-integration-policy.md",),
            ),
            ResidentDaemonPreflightItem(
                key="audit_event_schema_available",
                category=ResidentDaemonPreflightCategory.RELEASE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="Schema-only event records are available for future auditability.",
                evidence=("docs/architecture/resident-daemon-event-record-schema.md",),
            ),
        ),
    )
