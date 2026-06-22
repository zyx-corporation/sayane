"""Resident app-facing contract metadata for UI handoff."""

from __future__ import annotations

from typing import Any


def build_app_contract() -> dict[str, Any]:
    """Build a stable app-facing contract payload for UI implementers."""
    return {
        "kind": "resident_app_contract",
        "contract_version": "1",
        "preferred_entrypoint": "/app/overview",
        "human_surfaces": [
            {
                "path": "/app/ui",
                "format": "text/html",
                "purpose": "local bootstrap home screen",
            },
            {
                "path": "/app/ui/candidates",
                "format": "text/html",
                "purpose": "local candidate queue screen",
            },
            {
                "path": "/app/ui/capture-clipboard",
                "format": "form_post",
                "purpose": "local HTML clipboard capture action",
            },
            {
                "path": "/app/ui/daemon",
                "format": "text/html",
                "purpose": "local daemon panel screen",
            },
            {
                "path": "/app/ui-state/*",
                "format": "application/json",
                "purpose": "cookie-backed local UI screen-state reads for the Bridge-hosted local shell",
            },
            {
                "path": "/app/ui-action/*",
                "format": "application/json",
                "purpose": "cookie-backed local UI action writes for the Bridge-hosted local shell",
            },
        ],
        "read_surfaces": [
            {
                "path": "/app/overview",
                "payload_kind": "resident_app_overview",
                "purpose": "primary initial screen payload",
            },
            {
                "path": "/app/screen-state/home",
                "payload_kind": "resident_app_home_screen_state",
                "purpose": "framework-neutral home screen state",
            },
            {
                "path": "/app/daemon-overview",
                "payload_kind": "resident_daemon_overview_preview",
                "purpose": "focused daemon diagnostics panel",
            },
            {
                "path": "/app/operator-phase-status",
                "payload_kind": "resident_daemon_operator_phase_status",
                "purpose": "app-facing post-app operator packaging and supervision phase status read",
            },
            {
                "path": "cli:sayane app daemon-operator-phase-status --json",
                "payload_kind": "resident_daemon_operator_phase_status",
                "purpose": "aggregated post-app operator packaging and supervision phase status read",
            },
            {
                "path": "cli:sayane app daemon-packaging-status --json",
                "payload_kind": "resident_daemon_packaging_status",
                "purpose": "operator-facing packaging and supervision boundary read",
            },
            {
                "path": "cli:sayane app daemon-service-targets-status --json",
                "payload_kind": "resident_daemon_service_targets_status",
                "purpose": "cross-platform operator-facing service target status read",
            },
            {
                "path": "cli:sayane app daemon-service-control-boundary --json",
                "payload_kind": "resident_daemon_service_control_boundary",
                "purpose": "operator-facing allowed control and deferred service boundary read",
            },
            {
                "path": "cli:sayane app daemon-supervision-status --json",
                "payload_kind": "resident_daemon_supervision_status",
                "purpose": "operator-facing supervision UX status read",
            },
            {
                "path": "cli:sayane app daemon-launchagent-preview --json",
                "payload_kind": "resident_daemon_launchagent_plan",
                "purpose": "macOS LaunchAgent preview for the current local daemon line",
            },
            {
                "path": "cli:sayane app daemon-launchagent-status --json",
                "payload_kind": "resident_daemon_launchagent_status",
                "purpose": "macOS LaunchAgent status read for plist presence and current launchd loaded state",
            },
            {
                "path": "cli:sayane app daemon-recovery-consent-status --json",
                "payload_kind": "resident_daemon_recovery_consent_status",
                "purpose": "operator-facing recovery and consent boundary read",
            },
            {
                "path": "/app/screen-state/daemon",
                "payload_kind": "resident_app_daemon_panel_screen_state",
                "purpose": "framework-neutral daemon panel state",
            },
            {
                "path": "/app/candidates",
                "payload_kind": "resident_app_candidate_queue",
                "purpose": "reviewable candidate queue",
            },
            {
                "path": "/app/screen-state/candidates",
                "payload_kind": "resident_app_candidate_queue_screen_state",
                "purpose": "framework-neutral candidate queue state",
            },
            {
                "path": "/app/candidates/{id}",
                "payload_kind": "CandidateUpdate",
                "purpose": "candidate detail panel",
            },
            {
                "path": "/app/screen-state/candidates/{id}",
                "payload_kind": "resident_app_candidate_detail_screen_state",
                "purpose": "framework-neutral candidate detail state",
            },
            {
                "path": "/app/candidates/{id}/diff",
                "payload_kind": "candidate_diff",
                "purpose": "review diff panel",
            },
            {
                "path": "/app/ui-state/contract",
                "payload_kind": "resident_app_contract",
                "purpose": "cookie-backed local UI contract read for the Bridge-hosted local shell",
            },
            {
                "path": "/app/ui-state/home",
                "payload_kind": "resident_app_home_screen_state",
                "purpose": "cookie-backed local UI home screen state",
            },
            {
                "path": "/app/ui-state/operator-phase-status",
                "payload_kind": "resident_daemon_operator_phase_status",
                "purpose": "cookie-backed local UI operator phase status read",
            },
            {
                "path": "/app/ui-state/candidates",
                "payload_kind": "resident_app_candidate_queue_screen_state",
                "purpose": "cookie-backed local UI candidate queue state",
            },
            {
                "path": "/app/ui-state/candidates/{id}",
                "payload_kind": "resident_app_candidate_detail_screen_state",
                "purpose": "cookie-backed local UI candidate detail state",
            },
            {
                "path": "/app/ui-state/candidates/{id}/diff",
                "payload_kind": "candidate_diff",
                "purpose": "cookie-backed local UI candidate diff payload",
            },
            {
                "path": "/app/ui-state/candidates/{id}/lineage",
                "payload_kind": "candidate_lineage",
                "purpose": "cookie-backed local UI candidate lineage payload",
            },
            {
                "path": "/app/ui-state/daemon",
                "payload_kind": "resident_app_daemon_panel_screen_state",
                "purpose": "cookie-backed local UI daemon panel state",
            },
        ],
        "write_surfaces": [
            {
                "path": "/app/capture-clipboard",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "create pending candidate from clipboard",
            },
            {
                "path": "/app/candidates/{id}/evaluate",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "evaluate candidate in review flow",
            },
            {
                "path": "/app/candidates/{id}/revise",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "create revised pending candidate",
            },
            {
                "path": "/app/candidates/{id}/approve",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "approve candidate through review flow",
            },
            {
                "path": "/app/candidates/{id}/reject",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "reject candidate through review flow",
            },
            {
                "path": "/app/ui-action/capture-clipboard",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "cookie-backed local UI candidate creation from clipboard",
            },
            {
                "path": "/app/ui-action/candidates/{id}/evaluate",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "cookie-backed local UI candidate evaluation",
            },
            {
                "path": "/app/ui-action/candidates/{id}/revise",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "cookie-backed local UI revised pending candidate creation",
            },
            {
                "path": "/app/ui-action/candidates/{id}/approve",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "cookie-backed local UI candidate approval",
            },
            {
                "path": "/app/ui-action/candidates/{id}/reject",
                "method": "POST",
                "result_kind": "CandidateUpdate",
                "purpose": "cookie-backed local UI candidate rejection",
            },
            {
                "path": "/app/ui-action/session/logout",
                "method": "POST",
                "result_kind": "session_logout",
                "purpose": "cookie-backed local UI session invalidation for the Bridge-hosted local shell",
            },
        ],
        "recommended_flow": [
            "GET /app/overview",
            "POST /app/capture-clipboard",
            "GET /app/candidates",
            "GET /app/candidates/{id}",
            "GET /app/candidates/{id}/diff",
            "POST /app/candidates/{id}/evaluate",
            "POST /app/candidates/{id}/revise",
            "POST /app/candidates/{id}/approve or /reject",
            "GET /app/ui",
            "GET /app/ui-state/home",
            "GET /app/ui-state/operator-phase-status",
            "GET /app/ui-state/candidates",
            "GET /app/ui-state/candidates/{id}",
            "GET /app/ui-state/candidates/{id}/diff",
            "GET /app/ui-state/candidates/{id}/lineage",
            "GET /app/ui-state/daemon",
            "POST /app/ui-action/capture-clipboard",
            "POST /app/ui-action/candidates/{id}/evaluate",
            "POST /app/ui-action/candidates/{id}/revise",
            "POST /app/ui-action/candidates/{id}/approve or /reject",
            "POST /app/ui-action/session/logout",
        ],
        "screen_state_contracts": [
            {
                "screen": "home",
                "builder": "build_home_screen_state",
                "primary_source": "/app/overview",
            },
            {
                "screen": "candidate_queue",
                "builder": "build_candidate_queue_screen_state",
                "primary_source": "/app/candidates",
            },
            {
                "screen": "candidate_detail",
                "builder": "build_candidate_detail_screen_state",
                "primary_source": "/app/candidates/{id}",
            },
            {
                "screen": "daemon_panel",
                "builder": "build_daemon_panel_screen_state",
                "primary_source": "/app/daemon-overview",
            },
        ],
        "surface_roles": [
            {
                "surface": "resident_app",
                "role": "primary_growth_surface",
                "notes": [
                    "Bridge-hosted local shell is the primary operator-facing growth path",
                    "new workflow investment lands here first",
                ],
            },
            {
                "surface": "extension",
                "role": "compatibility_surface",
                "notes": [
                    "extension remains a compatibility path over shared app-facing contracts",
                    "extension-specific UX may diverge when host-container constraints require it",
                ],
            },
        ],
        "shared_semantics": [
            {
                "topic": "app_facing_endpoint_contracts",
                "shared_by_design": True,
                "notes": [
                    "extension and resident app read the same app-facing contract and screen-state surfaces",
                ],
            },
            {
                "topic": "screen_state_payload_semantics",
                "shared_by_design": True,
                "notes": [
                    "home, candidate queue, candidate detail, and daemon panel keep one semantic contract",
                ],
            },
            {
                "topic": "review_and_daemon_boundary_wording",
                "shared_by_design": True,
                "notes": [
                    "preview-or-review-only wording remains aligned across extension and resident app surfaces",
                ],
            },
            {
                "topic": "host_container_ux",
                "shared_by_design": False,
                "notes": [
                    "resident app and extension may keep different navigation and launch ergonomics",
                ],
            },
            {
                "topic": "auth_session_handling",
                "shared_by_design": False,
                "notes": [
                    "resident app uses a dedicated local UI session after bootstrap",
                    "extension keeps background-worker mediated Bridge auth instead of browser cookie sessions",
                ],
            },
        ],
        "operator_cli_surfaces": [
            {
                "command": "sayane app daemon-status --json",
                "purpose": "current daemon lifecycle status",
            },
            {
                "command": "sayane app daemon-operator-phase-status --json",
                "purpose": "aggregated packaging, service, supervision, and recovery phase status",
            },
            {
                "command": "sayane app daemon-packaging-status --json",
                "purpose": "current packaging and supervision boundary status",
            },
            {
                "command": "sayane app daemon-service-targets-status --json",
                "purpose": "cross-platform service target status for macOS, Linux, and Windows",
            },
            {
                "command": "sayane app daemon-service-control-boundary --json",
                "purpose": "current allowed control and deferred service-command boundary",
            },
            {
                "command": "sayane app daemon-supervision-status --json",
                "purpose": "current passive/active supervision UX boundary status",
            },
            {
                "command": "sayane app daemon-launchagent-preview --json",
                "purpose": "macOS LaunchAgent preview for writing a local service plist",
            },
            {
                "command": "sayane app daemon-launchagent-status --json",
                "purpose": "macOS LaunchAgent status read for explicit local service observation",
            },
            {
                "command": "sayane app daemon-launchagent-bootstrap --json",
                "purpose": "explicit local launchctl bootstrap after reviewed LaunchAgent plist write",
            },
            {
                "command": "sayane app daemon-launchagent-bootout --json",
                "purpose": "explicit local launchctl bootout for reviewed LaunchAgent rollback",
            },
            {
                "command": "sayane app daemon-launchagent-kickstart --json",
                "purpose": "explicit local launchctl kickstart for the reviewed resident LaunchAgent label",
            },
            {
                "command": "sayane app daemon-recovery-consent-status --json",
                "purpose": "current recovery flow and consent boundary status",
            },
            {
                "command": "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
                "purpose": "aggregated proof-oriented daemon diagnostics",
            },
        ],
        "boundaries": [
            "preview and review surfaces remain derived or candidate-scoped",
            "app-facing writes do not patch profile state directly",
            "daemon surfaces do not prove process identity, daemon readiness, or API readiness",
            "cookie-backed local UI shell reuses existing resident app semantics instead of introducing a parallel mutation model",
        ],
        "non_mvp_boundaries": [
            {
                "topic": "daemon_identity_proof",
                "status": "explicit_defer",
                "current_scope": "current resident app and daemon preview surfaces do not prove production daemon identity",
                "governing_docs": [
                    "docs/release/v1.0.8-resident-daemon-identity-preview.md",
                    "docs/architecture/resident-app-service-boundary.md",
                ],
            },
            {
                "topic": "daemon_readiness_and_api_readiness_proof",
                "status": "explicit_defer",
                "current_scope": "current resident app and daemon preview surfaces do not prove daemon readiness or API readiness",
                "governing_docs": [
                    "docs/architecture/resident-daemon-readiness-and-api-readiness-policy.md",
                    "docs/release/v1.0.14-resident-app-operator-handoff.md",
                ],
            },
            {
                "topic": "os_service_integration_ui",
                "status": "separate_plan",
                "current_scope": "current release line excludes OS service installation, supervision, and service-oriented operator UI",
                "governing_docs": [
                    "docs/release/v1.0.14-resident-app-operator-handoff.md",
                    "docs/release/v1.0.15-operator-packaging-supervision-phase-plan.md",
                ],
            },
            {
                "topic": "tray_or_background_supervision_ui",
                "status": "separate_plan",
                "current_scope": "current release line excludes tray, menu-bar, and background supervision UX",
                "governing_docs": [
                    "docs/release/v1.0.14-resident-app-operator-handoff.md",
                    "docs/release/v1.0.15-operator-packaging-supervision-phase-plan.md",
                ],
            },
            {
                "topic": "direct_profile_patch_ui",
                "status": "explicit_defer",
                "current_scope": "current app-facing writes remain inside candidate review and do not patch profile state directly",
                "governing_docs": [
                    "docs/architecture/resident-app-ui-integration-contract.md",
                    "docs/release/v1.0.14-resident-app-operator-handoff.md",
                ],
            },
        ],
    }
