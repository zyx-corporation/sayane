import Foundation
import Testing
@testable import SayaneApp

@Test func queueStateDecodesRepresentativePayload() throws {
    let data = Data(#"""
    {
      "kind": "resident_app_candidate_queue_screen_state",
      "reviewable_count": 2,
      "status_counts": {"pending": 1, "evaluated": 1},
      "top_sections": [{"section": "knowledge.concepts", "count": 2}],
      "items": [
        {"id": "cand-001", "status": "pending", "section": "knowledge.concepts", "content": "A", "display_summary": "alpha"},
        {"id": "cand-002", "status": "evaluated", "section": "knowledge.preferences", "content": "B", "display_summary": "beta"}
      ]
    }
    """#.utf8)
    let payload = try JSONDecoder().decode(CandidateQueueScreenState.self, from: data)
    #expect(payload.reviewableCount == 2)
    #expect(payload.items.first?.id == "cand-001")
    #expect(payload.topSections.first?.section == "knowledge.concepts")
}

@Test func daemonStateDecodesOperatorPhasePayload() throws {
    let data = Data(#"""
    {
      "kind": "resident_app_daemon_panel_screen_state",
      "summary_cards": [{"key": "state", "value": "running"}],
      "operator_panels": [{"panel": "packaging_status", "title": "packaging_status", "status": "cli_first_local_bridge", "highlights": ["manual", "in_progress"]}],
      "service_target_summary": {"current_platform": "macos", "recommended_target": "launchagent", "targets": [{"target": "macos_launchagent", "status": "available"}]},
      "launchagent_summary": {"preview_available": true, "status_available": true, "plist_path": "/tmp/test.plist", "loaded_status": "loaded", "launchctl_commands": {"bootstrap": "launchctl bootstrap"}},
      "launchagent_preview": {
        "operation_id": "launchagent-123456",
        "preview_hash": "abc123def456",
        "label": "com.sayane.resident.bridge",
        "plist_path": "/tmp/test.plist",
        "stdout_path": "/tmp/runtime/log/out.log",
        "stderr_path": "/tmp/runtime/log/err.log",
        "program_arguments": ["/usr/bin/python3", "-m", "sayane.cli.main", "serve", "--host", "127.0.0.1", "--port", "38741"],
        "plist_xml": "<plist>...</plist>"
      },
      "launchagent_status": {
        "loaded": true,
        "print_command": "launchctl print gui/501/com.sayane.resident.bridge",
        "returncode": 0,
        "plist_exists": true,
        "stderr": ""
      },
      "packaging_status": {
        "packaging_model": "cli_first_local_bridge",
        "packaging_decision": {
          "candidate_models": [
            {"model": "cli_first_local_bridge", "status": "current_supported_line", "operator_value": "lowest change", "blocked_by": []},
            {"model": "hybrid_local_bridge_plus_service_targets", "status": "candidate_requires_phase_closure", "operator_value": "hybrid", "blocked_by": ["service lifecycle implementation"]}
          ],
          "decision_guardrails": ["do not smuggle service-first commitments into app-shell polish"]
        }
      },
      "service_control_boundary": {
        "control_plane": {"allowed_commands": [{"command": "sayane app daemon-start --json"}]},
        "service_plane": {
          "deferred_commands": ["daemon-service-install"],
          "lifecycle_operations": [
            {"operation": "install", "command": "daemon-service-install", "status": "separate_plan_required", "platform_scope": ["macos_launchagent"], "rollback_required": true, "policy_required": true}
          ]
        },
        "app_ui_policy": {
          "allowed_reads": ["/app/overview"],
          "forbidden_control_exposure": ["direct OS service install/enable/disable actions"]
        },
        "governing_rules": ["service commands remain deferred until platform-specific rollback policy exists"]
      },
      "service_targets_status": {
        "policy_gates": {"platform_policy_required": true, "rollback_policy_required": true},
        "targets": [{"target": "macos_launchagent", "platform": "macos", "status": "supported_preview_apply_control", "blocked_by": ["rollback policy"]}]
      },
      "supervision_status": {
        "supervision_mode": "passive_local_observation_with_cli_recovery",
        "passive_visibility": {"surfaces": ["/app/overview"]},
        "active_supervision": {"allowed_actions": ["sayane app daemon-start --json"]},
        "background_surfaces": {"candidate_surfaces": [{"surface": "menu_bar_supervision", "status": "separate_plan_required", "platform_scope": ["macos"], "operator_value": "local visibility", "forbidden_capabilities": ["silent launchctl mutation"]}]},
        "ux_guardrails": ["current supervision line stays local-only and CLI-compatible"]
      },
      "recovery_consent_status": {
        "consent_model": "explicit_cli_confirmation_for_mutation",
        "recovery_model": "diagnose_then_operator_review_then_cli_action",
        "non_mutating_diagnostics": ["sayane app daemon-status --json"],
        "control_recovery_actions": [{"command": "sayane app daemon-start --json", "notes": ["runtime init must already be complete"]}],
        "recommended_recovery_flow": ["inspect current status and proof-oriented diagnostics"],
        "app_ui_guardrails": ["local app UI may expose read-only recovery guidance but not destructive consent bypasses"]
      },
      "operator_phase_status": {
        "phase": "post_app",
        "current_supported_operator_path": {
          "startup_command_text": "sayane serve --host 127.0.0.1 --port 38741",
          "bootstrap_ui": "http://127.0.0.1:38741/app/ui",
          "local_only": true,
          "notes": ["current supported operator path remains local Python CLI plus Local Bridge"]
        },
        "workstreams": [
          {"name": "supervision_ux_line", "status": "limited_cli_only", "background_status": "not_supported"}
        ],
        "phase_closure_checklist": [
          {"item": "supported_packaging_model_finalized", "status": "in_progress", "blocking_reasons": ["hybrid and service-first candidates remain explicitly open"]}
        ]
      },
      "operator_phase_summary": {"phase": "post_app", "phase_status": "in_progress", "phase_readiness": "not_ready_for_phase_closure", "blocking_reasons": ["service_integration"], "checklist": ["packaging"]},
      "operator_phase_details": {
        "current_supported_operator_path": {"startup_command_text": "sayane serve", "bootstrap_ui": "http://127.0.0.1:38741/app/ui", "local_only": true, "notes": ["local only"]},
        "workstreams": [{"name": "packaging_model_decision", "status": "in_progress", "detail": "cli_first_local_bridge"}],
        "recommended_implementation_order": ["packaging"],
        "read_surfaces": ["/app/ui-state/daemon"],
        "exit_criteria": ["decide model"],
        "not_in_scope": ["windows app"]
      },
      "next_actions": [{"command": "sayane app daemon-launchagent-status --json", "reason": "Observe launchd state."}],
      "runtime_init": {"runtime_root": "/tmp/runtime", "review_required": false, "items": [{"path": "/tmp/runtime/log"}]},
      "cleanup_preview": {"decision_report": {"decisions": [{"recommended_action": "remove"}, {"recommended_action": "keep"}]}},
      "repair_preview": {"decisions": {"log_dir": {"status": "missing"}}}
    }
    """#.utf8)
    let payload = try JSONDecoder().decode(DaemonPanelScreenState.self, from: data)
    #expect(payload.operatorPhaseSummary.phaseReadiness == "not_ready_for_phase_closure")
    #expect(payload.operatorPhaseDetails.workstreams.first?.name == "packaging_model_decision")
    #expect(payload.serviceTargetSummary.currentPlatform == "macos")
    #expect(payload.nextActions.first?.command == "sayane app daemon-launchagent-status --json")
    #expect(payload.launchagentStatus?["loaded"]?.boolValue == true)
    #expect(payload.launchagentPreview?["stdout_path"]?.stringValue == "/tmp/runtime/log/out.log")
    #expect(payload.launchagentPreview?["operation_id"]?.stringValue == "launchagent-123456")
    #expect(payload.launchagentPreview?["preview_hash"]?.stringValue == "abc123def456")
    #expect(payload.packagingStatus?["packaging_model"]?.stringValue == "cli_first_local_bridge")
    #expect(payload.supervisionStatus?["supervision_mode"]?.stringValue == "passive_local_observation_with_cli_recovery")
    #expect(payload.recoveryConsentStatus?["consent_model"]?.stringValue == "explicit_cli_confirmation_for_mutation")
    #expect(payload.operatorPhaseStatus?["current_supported_operator_path"]?.objectValue?["local_only"]?.boolValue == true)
}
