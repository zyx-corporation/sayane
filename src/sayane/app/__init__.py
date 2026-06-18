"""Resident app service boundary for ADR 0007 Phase 4."""

from sayane.app.capabilities import (
    CapabilityIssuer,
    CapabilityIssuerPolicy,
    CapabilityToken,
    create_capability_issuer_for_surface,
    create_local_capability_token,
    create_surface_capability_tokens,
)
from sayane.app.daemon_cleanup_decisions import (
    ResidentDaemonCleanupDecision,
    ResidentDaemonCleanupDecisionReport,
    ResidentDaemonCleanupRecommendation,
    build_cleanup_decision,
    build_cleanup_decision_report,
)
from sayane.app.daemon_event_records import (
    ResidentDaemonEventCategory,
    ResidentDaemonEventRecord,
    ResidentDaemonEventResult,
    build_preflight_event_record,
    build_runtime_init_event_record,
)
from sayane.app.daemon_identity import (
    ResidentDaemonIdentity,
    validate_runtime_local_path,
)
from sayane.app.daemon_lifecycle import (
    ResidentDaemonLifecycle,
    ResidentDaemonMode,
    ResidentDaemonState,
    is_local_bind_host,
    validate_local_bind_host,
)
from sayane.app.daemon_liveness_diagnostics import (
    ResidentDaemonLivenessDiagnostic,
    ResidentDaemonLivenessStatus,
    build_liveness_diagnostic,
    build_liveness_diagnostic_from_pid_file_diagnostic,
)
from sayane.app.daemon_pid_diagnostics import (
    ResidentDaemonPidFileDiagnostic,
    ResidentDaemonPidParseStatus,
    build_pid_file_diagnostic,
)
from sayane.app.daemon_preflight import (
    ResidentDaemonPreflightCategory,
    ResidentDaemonPreflightItem,
    ResidentDaemonPreflightReport,
    ResidentDaemonPreflightStatus,
    build_implementation_gate_preflight_report,
)
from sayane.app.daemon_runtime_init import (
    ResidentDaemonRuntimeInitItem,
    ResidentDaemonRuntimeInitPlan,
    ResidentDaemonRuntimeInitStatus,
    apply_runtime_init,
    build_runtime_init_plan,
)
from sayane.app.daemon_runtime_layout import (
    ResidentDaemonRuntimeLayout,
    validate_runtime_child_path,
)
from sayane.app.daemon_runtime_metadata import (
    ResidentDaemonRuntimeInitMetadata,
    build_runtime_init_metadata,
)
from sayane.app.daemon_stale_artifacts import (
    ResidentDaemonArtifactDiagnostic,
    ResidentDaemonArtifactKind,
    ResidentDaemonArtifactStatus,
    ResidentDaemonStaleArtifactReport,
    build_stale_artifact_report,
)
from sayane.app.daemon_state_machine import (
    ResidentDaemonStateMachine,
    ResidentDaemonStateMachineState,
    ResidentDaemonStateMachineTransition,
    build_resident_daemon_state_machine,
)
from sayane.app.runtime import (
    ResidentRepositoryBackend,
    ResidentRepositorySelection,
    ResidentRuntime,
    build_resident_runtime,
    select_resident_repositories,
)
from sayane.app.service import ResidentAppService
from sayane.app.ui import build_mcp_preview, build_review_queue

__all__ = [
    "CapabilityIssuer",
    "CapabilityIssuerPolicy",
    "CapabilityToken",
    "ResidentAppService",
    "ResidentDaemonArtifactDiagnostic",
    "ResidentDaemonArtifactKind",
    "ResidentDaemonArtifactStatus",
    "ResidentDaemonCleanupDecision",
    "ResidentDaemonCleanupDecisionReport",
    "ResidentDaemonCleanupRecommendation",
    "ResidentDaemonEventCategory",
    "ResidentDaemonEventRecord",
    "ResidentDaemonEventResult",
    "ResidentDaemonIdentity",
    "ResidentDaemonLifecycle",
    "ResidentDaemonLivenessDiagnostic",
    "ResidentDaemonLivenessStatus",
    "ResidentDaemonMode",
    "ResidentDaemonPidFileDiagnostic",
    "ResidentDaemonPidParseStatus",
    "ResidentDaemonPreflightCategory",
    "ResidentDaemonPreflightItem",
    "ResidentDaemonPreflightReport",
    "ResidentDaemonPreflightStatus",
    "ResidentDaemonRuntimeLayout",
    "ResidentDaemonRuntimeInitItem",
    "ResidentDaemonRuntimeInitPlan",
    "ResidentDaemonRuntimeInitStatus",
    "ResidentDaemonRuntimeInitMetadata",
    "ResidentDaemonStateMachine",
    "ResidentDaemonStateMachineState",
    "ResidentDaemonStateMachineTransition",
    "ResidentDaemonStaleArtifactReport",
    "ResidentDaemonState",
    "ResidentRepositoryBackend",
    "ResidentRepositorySelection",
    "ResidentRuntime",
    "build_cleanup_decision",
    "build_cleanup_decision_report",
    "build_implementation_gate_preflight_report",
    "build_liveness_diagnostic",
    "build_liveness_diagnostic_from_pid_file_diagnostic",
    "build_mcp_preview",
    "build_pid_file_diagnostic",
    "build_preflight_event_record",
    "build_runtime_init_event_record",
    "build_resident_runtime",
    "build_resident_daemon_state_machine",
    "build_runtime_init_plan",
    "build_runtime_init_metadata",
    "build_review_queue",
    "build_stale_artifact_report",
    "create_capability_issuer_for_surface",
    "create_local_capability_token",
    "create_surface_capability_tokens",
    "apply_runtime_init",
    "is_local_bind_host",
    "select_resident_repositories",
    "validate_local_bind_host",
    "validate_runtime_child_path",
    "validate_runtime_local_path",
]
