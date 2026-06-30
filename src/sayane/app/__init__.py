"""Resident app service boundary for ADR 0007 Phase 4."""

from sayane.app.app_candidate_views import (
    build_app_candidate_detail,
    build_app_candidate_diff,
    build_app_candidate_queue,
)
from sayane.app.app_contract import build_app_contract
from sayane.app.app_overview import build_app_overview
from sayane.app.app_screen_states import (
    build_candidate_detail_screen_state,
    build_candidate_queue_screen_state,
    build_daemon_panel_screen_state,
    build_home_screen_state,
)
from sayane.app.capabilities import (
    CapabilityIssuer,
    CapabilityIssuerPolicy,
    CapabilityToken,
    create_capability_issuer_for_surface,
    create_local_capability_token,
    create_surface_capability_tokens,
)
from sayane.app.daemon_api_readiness_proof import (
    ResidentDaemonApiReadinessProof,
    ResidentDaemonApiReadinessProofStatus,
    build_api_readiness_proof,
    build_api_readiness_proof_from_status_report,
)
from sayane.app.daemon_cleanup_apply import (
    ResidentDaemonCleanupApplyError,
    ResidentDaemonCleanupApplyTarget,
    apply_cleanup_decisions,
    build_cleanup_apply_preview,
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
    build_cleanup_apply_event_record,
    build_preflight_event_record,
    build_process_control_event_record,
    build_readiness_event_record,
    build_repair_apply_event_record,
    build_runtime_init_event_record,
)
from sayane.app.daemon_identity import (
    ResidentDaemonIdentity,
    validate_runtime_local_path,
)
from sayane.app.daemon_identity_proof import (
    ResidentDaemonIdentityProof,
    ResidentDaemonIdentityProofStatus,
    build_identity_proof,
    build_identity_proof_from_status_report,
)
from sayane.app.daemon_launchagent import (
    LAUNCHAGENT_LABEL,
    ResidentDaemonLaunchAgentApplyError,
    ResidentDaemonLaunchAgentControlError,
    ResidentDaemonLaunchAgentPlan,
    apply_launchagent_plan,
    build_launchagent_plan,
    build_launchagent_status,
    run_launchagent_command,
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
from sayane.app.daemon_operator_phase_status import (
    ResidentDaemonOperatorPhaseStatus,
    build_daemon_operator_phase_status,
)
from sayane.app.daemon_packaging_status import (
    ResidentDaemonPackagingStatus,
    build_daemon_packaging_status,
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
from sayane.app.daemon_process_control import (
    ResidentDaemonProcessControlError,
    ResidentDaemonProcessControlReceipt,
    ResidentDaemonProcessStatusReport,
    build_daemon_status_report,
    restart_resident_daemon,
    start_resident_daemon,
    stop_resident_daemon,
)
from sayane.app.daemon_proof_status import (
    ResidentDaemonProofDowngradeReason,
    ResidentDaemonProofStatus,
)
from sayane.app.daemon_readiness_diagnostics import (
    ResidentDaemonApiReadinessStatus,
    ResidentDaemonReadinessDiagnostic,
    ResidentDaemonReadinessStatus,
    build_readiness_diagnostic,
    build_readiness_diagnostic_from_status_report,
)
from sayane.app.daemon_readiness_proof import (
    ResidentDaemonReadinessProof,
    ResidentDaemonReadinessProofStatus,
    build_readiness_proof,
    build_readiness_proof_from_status_report,
)
from sayane.app.daemon_recovery_consent_status import (
    ResidentDaemonRecoveryConsentStatus,
    build_daemon_recovery_consent_status,
)
from sayane.app.daemon_repair_apply import (
    ResidentDaemonRepairApplyError,
    ResidentDaemonRepairApplyTarget,
    apply_runtime_repairs,
    build_repair_apply_preview,
)
from sayane.app.daemon_runtime_init import (
    ResidentDaemonRuntimeInitApplyError,
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
from sayane.app.daemon_runtime_receipts import (
    ResidentDaemonRuntimeInitReceipt,
    build_runtime_init_receipt,
)
from sayane.app.daemon_service_control_boundary import (
    ResidentDaemonServiceControlBoundary,
    build_daemon_service_control_boundary,
)
from sayane.app.daemon_service_targets_status import (
    ResidentDaemonServiceTargetsStatus,
    build_daemon_service_targets_status,
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
from sayane.app.daemon_supervision_status import (
    ResidentDaemonSupervisionStatus,
    build_daemon_supervision_status,
)
from sayane.app.daemon_systemd_user import (
    SYSTEMD_USER_UNIT_NAME,
    ResidentDaemonSystemdUserApplyError,
    ResidentDaemonSystemdUserControlError,
    ResidentDaemonSystemdUserPlan,
    apply_systemd_user_plan,
    build_systemd_user_plan,
    build_systemd_user_status,
    run_systemd_user_command,
)
from sayane.app.runtime import (
    ResidentRepositoryBackend,
    ResidentRepositorySelection,
    ResidentRuntime,
    build_resident_runtime,
    select_resident_repositories,
)
from sayane.app.service import ResidentAppService
from sayane.app.ui import (
    build_daemon_overview_preview,
    build_mcp_preview,
    build_review_queue,
)
from sayane.app.vault_session_status import build_app_vault_session_status
from sayane.app.vault_status import build_app_vault_status

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
    "ResidentDaemonCleanupApplyError",
    "ResidentDaemonCleanupApplyTarget",
    "ResidentDaemonEventCategory",
    "ResidentDaemonEventRecord",
    "ResidentDaemonEventResult",
    "ResidentDaemonIdentity",
    "ResidentDaemonIdentityProof",
    "ResidentDaemonIdentityProofStatus",
    "ResidentDaemonLifecycle",
    "ResidentDaemonLaunchAgentApplyError",
    "ResidentDaemonLaunchAgentControlError",
    "ResidentDaemonLaunchAgentPlan",
    "ResidentDaemonLivenessDiagnostic",
    "ResidentDaemonLivenessStatus",
    "ResidentDaemonMode",
    "ResidentDaemonOperatorPhaseStatus",
    "ResidentDaemonPackagingStatus",
    "ResidentDaemonPidFileDiagnostic",
    "ResidentDaemonPidParseStatus",
    "ResidentDaemonProcessControlError",
    "ResidentDaemonProcessControlReceipt",
    "ResidentDaemonProcessStatusReport",
    "ResidentDaemonPreflightCategory",
    "ResidentDaemonPreflightItem",
    "ResidentDaemonPreflightReport",
    "ResidentDaemonPreflightStatus",
    "ResidentDaemonApiReadinessStatus",
    "ResidentDaemonApiReadinessProof",
    "ResidentDaemonApiReadinessProofStatus",
    "ResidentDaemonProofDowngradeReason",
    "ResidentDaemonProofStatus",
    "ResidentDaemonReadinessDiagnostic",
    "ResidentDaemonReadinessProof",
    "ResidentDaemonReadinessProofStatus",
    "ResidentDaemonReadinessStatus",
    "ResidentDaemonRecoveryConsentStatus",
    "ResidentDaemonRuntimeLayout",
    "ResidentDaemonRuntimeInitItem",
    "ResidentDaemonRuntimeInitApplyError",
    "ResidentDaemonRuntimeInitPlan",
    "ResidentDaemonRuntimeInitStatus",
    "ResidentDaemonRuntimeInitMetadata",
    "ResidentDaemonRuntimeInitReceipt",
    "ResidentDaemonServiceControlBoundary",
    "ResidentDaemonServiceTargetsStatus",
    "ResidentDaemonSystemdUserApplyError",
    "ResidentDaemonSystemdUserControlError",
    "ResidentDaemonSystemdUserPlan",
    "ResidentDaemonRepairApplyError",
    "ResidentDaemonRepairApplyTarget",
    "ResidentDaemonStateMachine",
    "ResidentDaemonStateMachineState",
    "ResidentDaemonStateMachineTransition",
    "ResidentDaemonStaleArtifactReport",
    "ResidentDaemonState",
    "ResidentDaemonSupervisionStatus",
    "ResidentRepositoryBackend",
    "ResidentRepositorySelection",
    "ResidentRuntime",
    "LAUNCHAGENT_LABEL",
    "SYSTEMD_USER_UNIT_NAME",
    "build_api_readiness_proof",
    "build_api_readiness_proof_from_status_report",
    "apply_launchagent_plan",
    "apply_systemd_user_plan",
    "run_systemd_user_command",
    "run_launchagent_command",
    "build_launchagent_status",
    "build_app_candidate_detail",
    "build_app_candidate_diff",
    "build_app_candidate_queue",
    "build_app_contract",
    "build_app_overview",
    "build_app_vault_session_status",
    "build_app_vault_status",
    "build_candidate_detail_screen_state",
    "build_candidate_queue_screen_state",
    "build_cleanup_decision",
    "build_cleanup_decision_report",
    "apply_cleanup_decisions",
    "apply_runtime_repairs",
    "build_cleanup_apply_preview",
    "build_cleanup_apply_event_record",
    "build_implementation_gate_preflight_report",
    "build_liveness_diagnostic",
    "build_liveness_diagnostic_from_pid_file_diagnostic",
    "build_launchagent_plan",
    "build_systemd_user_plan",
    "build_systemd_user_status",
    "build_daemon_packaging_status",
    "build_mcp_preview",
    "build_home_screen_state",
    "build_identity_proof",
    "build_identity_proof_from_status_report",
    "build_process_control_event_record",
    "build_readiness_diagnostic",
    "build_readiness_diagnostic_from_status_report",
    "build_readiness_proof",
    "build_readiness_proof_from_status_report",
    "build_daemon_recovery_consent_status",
    "build_readiness_event_record",
    "build_daemon_status_report",
    "build_daemon_service_control_boundary",
    "build_daemon_service_targets_status",
    "build_daemon_overview_preview",
    "build_daemon_operator_phase_status",
    "build_pid_file_diagnostic",
    "build_preflight_event_record",
    "build_runtime_init_event_record",
    "build_repair_apply_event_record",
    "build_repair_apply_preview",
    "build_resident_runtime",
    "build_resident_daemon_state_machine",
    "build_daemon_panel_screen_state",
    "build_runtime_init_plan",
    "build_runtime_init_metadata",
    "build_runtime_init_receipt",
    "build_review_queue",
    "build_stale_artifact_report",
    "build_daemon_supervision_status",
    "create_capability_issuer_for_surface",
    "create_local_capability_token",
    "create_surface_capability_tokens",
    "apply_runtime_init",
    "is_local_bind_host",
    "restart_resident_daemon",
    "select_resident_repositories",
    "start_resident_daemon",
    "stop_resident_daemon",
    "validate_local_bind_host",
    "validate_runtime_child_path",
    "validate_runtime_local_path",
]
