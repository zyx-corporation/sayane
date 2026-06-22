"""Shared conservative resident daemon proof status vocabulary."""

from __future__ import annotations

from enum import StrEnum


class ResidentDaemonProofStatus(StrEnum):
    """Shared conservative proof statuses across identity/readiness/API layers."""

    MANUAL_REVIEW_REQUIRED = "manual_review_required"
    IDENTITY_NOT_RUNNING = "identity_not_running"
    IDENTITY_UNVERIFIED = "identity_unverified"
    READINESS_NOT_READY = "readiness_not_ready"
    READINESS_UNVERIFIED = "readiness_unverified"
    READINESS_DEGRADED = "readiness_degraded"
    API_UNREACHABLE = "api_unreachable"
    API_UNAUTHENTICATED = "api_unauthenticated"
    API_READINESS_UNVERIFIED = "api_readiness_unverified"


class ResidentDaemonProofDowngradeReason(StrEnum):
    """Shared explicit downgrade reasons across proof layers."""

    PROCESS_STATUS_REQUIRES_MANUAL_REVIEW = "process_status_requires_manual_review"
    NO_RUNNING_PROCESS = "no_running_process"
    UNAUTHENTICATED_HEALTH_ENDPOINT_ONLY = "unauthenticated_health_endpoint_only"
    PROCESS_EXISTENCE_WITHOUT_IDENTITY_PROOF = "process_existence_without_identity_proof"
    PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_READINESS = (
        "process_existence_without_authenticated_readiness"
    )
    PROCESS_EXISTENCE_WITHOUT_AUTHENTICATED_API_REACHABILITY = (
        "process_existence_without_authenticated_api_reachability"
    )
