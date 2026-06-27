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
        "operator_surface": {
          "primary_ui": "native_macos_app_primary",
          "debug_ui": "bridge_hosted_debug_shell",
          "recommended_launcher": {
            "command_text": "./scripts/run-macos-app-preview.sh"
          },
          "notes": ["native macOS app is the primary operator-facing UI on macOS"]
        },
        "packaging_decision": {
          "candidate_models": [
            {"model": "cli_first_local_bridge", "status": "current_supported_line", "operator_value": "lowest change", "blocked_by": []},
            {"model": "hybrid_local_bridge_plus_service_targets", "status": "candidate_requires_phase_closure", "operator_value": "hybrid", "blocked_by": ["service lifecycle implementation"]},
            {"model": "service_first_resident_runtime", "status": "candidate_requires_larger_architecture_change", "operator_value": "service-first", "blocked_by": ["auth/runtime model redesign"]}
          ],
          "decision_guardrails": ["do not smuggle service-first commitments into app-shell polish"]
        }
      },
      "service_control_boundary": {
        "control_plane": {
          "allowed_commands": [{"command": "sayane app daemon-start --json"}],
          "recovery_policy": ["review status and logs first"]
        },
        "service_plane": {
          "deferred_commands": ["daemon-service-install"],
          "platform_targets": ["macos_launchagent", "linux_systemd_user", "windows_service"],
          "lifecycle_operations": [
            {"operation": "install", "command": "daemon-service-install", "status": "separate_plan_required", "platform_scope": ["macos_launchagent"], "rollback_required": true, "policy_required": true}
          ]
        },
        "app_ui_policy": {
          "allowed_reads": ["/app/overview"],
          "allowed_writes": [],
          "allowed_control_exposure": ["daemon-start may appear as a next action"],
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
        "active_supervision": {"allowed_actions": ["sayane app daemon-start --json"], "app_ui_actions": []},
        "background_surfaces": {"deferred_topics": ["menu_bar_supervision"], "candidate_surfaces": [{"surface": "menu_bar_supervision", "status": "separate_plan_required", "platform_scope": ["macos"], "operator_value": "local visibility", "forbidden_capabilities": ["silent launchctl mutation"]}]},
        "recovery_entrypoints": ["sayane app daemon-status --json"],
        "ux_guardrails": ["current supervision line stays local-only and CLI-compatible"]
      },
      "recovery_consent_status": {
        "consent_model": "explicit_cli_confirmation_for_mutation",
        "recovery_model": "diagnose_then_operator_review_then_cli_action",
        "non_mutating_diagnostics": ["sayane app daemon-status --json"],
        "mutating_recovery_actions": [{"command": "sayane app daemon-runtime-init --apply --json", "consent_required": true, "scope": "runtime initialization artifacts"}],
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
        "current_supported_operator_path": {"startup_command_text": "sayane serve", "primary_operator_ui": "native_macos_app_primary", "debug_operator_ui": "bridge_hosted_debug_shell", "recommended_launcher": "./scripts/run-macos-app-preview.sh", "bootstrap_ui": "http://127.0.0.1:38741/app/ui", "local_only": true, "notes": ["local only"]},
        "workstreams": [{"name": "packaging_model_decision", "status": "in_progress", "detail": "cli_first_local_bridge"}],
        "recommended_implementation_order": ["packaging"],
        "decision_assist": [{"topic": "packaging_model_decision", "summary": "keep current line explicit", "command": "sayane app daemon-packaging-status --json"}],
        "read_surfaces": ["/app/ui-state/daemon"],
        "closure_evidence": [{"surface": "operator_phase_status", "command": "sayane app daemon-operator-phase-status --json", "confirms": "phase readiness"}],
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
    #expect(payload.operatorPhaseDetails.currentSupportedOperatorPath.primaryOperatorUI == "native_macos_app_primary")
    #expect(payload.operatorPhaseDetails.currentSupportedOperatorPath.recommendedLauncher == "./scripts/run-macos-app-preview.sh")
    #expect(payload.operatorPhaseDetails.decisionAssist?.first?.topic == "packaging_model_decision")
    #expect(payload.operatorPhaseDetails.closureEvidence?.first?.surface == "operator_phase_status")
    #expect(payload.serviceTargetSummary.currentPlatform == "macos")
    #expect(payload.nextActions.first?.command == "sayane app daemon-launchagent-status --json")
    #expect(payload.launchagentStatus?["loaded"]?.boolValue == true)
    #expect(payload.launchagentPreview?["stdout_path"]?.stringValue == "/tmp/runtime/log/out.log")
    #expect(payload.launchagentPreview?["operation_id"]?.stringValue == "launchagent-123456")
    #expect(payload.launchagentPreview?["preview_hash"]?.stringValue == "abc123def456")
    #expect(payload.packagingStatus?["packaging_model"]?.stringValue == "cli_first_local_bridge")
    #expect(payload.packagingStatus?["operator_surface"]?.objectValue?["primary_ui"]?.stringValue == "native_macos_app_primary")
    #expect(payload.packagingStatus?["operator_surface"]?.objectValue?["debug_ui"]?.stringValue == "bridge_hosted_debug_shell")
    #expect(payload.packagingStatus?["operator_surface"]?.objectValue?["recommended_launcher"]?.objectValue?["command_text"]?.stringValue == "./scripts/run-macos-app-preview.sh")
    #expect(payload.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?.count == 3)
    #expect(payload.packagingStatus?["packaging_decision"]?.objectValue?["candidate_models"]?.arrayValue?[2].objectValue?["model"]?.stringValue == "service_first_resident_runtime")
    #expect(payload.serviceControlBoundary?["control_plane"]?.objectValue?["recovery_policy"]?.arrayValue?.first?.stringValue == "review status and logs first")
    #expect(payload.serviceControlBoundary?["service_plane"]?.objectValue?["platform_targets"]?.arrayValue?.count == 3)
    #expect(payload.serviceControlBoundary?["app_ui_policy"]?.objectValue?["allowed_control_exposure"]?.arrayValue?.first?.stringValue == "daemon-start may appear as a next action")
    #expect(payload.supervisionStatus?["supervision_mode"]?.stringValue == "passive_local_observation_with_cli_recovery")
    #expect(payload.supervisionStatus?["background_surfaces"]?.objectValue?["deferred_topics"]?.arrayValue?.first?.stringValue == "menu_bar_supervision")
    #expect(payload.supervisionStatus?["recovery_entrypoints"]?.arrayValue?.first?.stringValue == "sayane app daemon-status --json")
    #expect(payload.recoveryConsentStatus?["consent_model"]?.stringValue == "explicit_cli_confirmation_for_mutation")
    #expect(payload.recoveryConsentStatus?["mutating_recovery_actions"]?.arrayValue?.first?.objectValue?["scope"]?.stringValue == "runtime initialization artifacts")
    #expect(payload.operatorPhaseStatus?["current_supported_operator_path"]?.objectValue?["local_only"]?.boolValue == true)
}

@Test func homeStateDecodesVaultSummaryPayload() throws {
    let data = Data(#"""
    {
      "kind": "resident_app_home_screen_state",
      "summary_cards": [
        {"key": "vault_status", "value": "available"},
        {"key": "vault_backend", "value": "sqlite_macos_keychain_vault"},
        {"key": "vault_assurance", "value": "os_backed"}
      ],
      "top_review_items": [],
      "top_daemon_actions": ["sayane app daemon-status --json"],
      "vault_summary": {
        "status": "available",
        "backend": "sqlite_macos_keychain_vault",
        "assurance": "os_backed",
        "vault_path": "/tmp/sayane/vault/main.sqlite",
        "supports_scoped_unlock_sessions": true,
        "recommended_setup": {
          "status": "sayane vault status --macos-keychain --sqlite /tmp/sayane/vault/main.sqlite --json"
        },
        "unlock_policies": [
          {
            "level": "normal",
            "idle_timeout_seconds": 900,
            "absolute_timeout_seconds": 28800,
            "requires_explicit_unlock": true,
            "scopes": ["candidate_review", "candidate_write"]
          }
        ],
        "notes": ["Local Vault is available to the resident app runtime."]
      },
      "quick_links": [{"screen": "candidate_queue", "path": "/app/candidates"}]
    }
    """#.utf8)
    let payload = try JSONDecoder().decode(HomeScreenState.self, from: data)
    #expect(payload.vaultSummary?.status == "available")
    #expect(payload.vaultSummary?.backend == "sqlite_macos_keychain_vault")
    #expect(payload.vaultSummary?.assurance == "os_backed")
    #expect(payload.vaultSummary?.vaultPath == "/tmp/sayane/vault/main.sqlite")
    #expect(payload.vaultSummary?.supportsScopedUnlockSessions == true)
    #expect(payload.vaultSummary?.recommendedSetup?["status"] == "sayane vault status --macos-keychain --sqlite /tmp/sayane/vault/main.sqlite --json")
    #expect(payload.vaultSummary?.unlockPolicies.count == 1)
    #expect(payload.vaultSummary?.unlockPolicies.first?.level == "normal")
    #expect(payload.vaultSummary?.unlockPolicies.first?.scopes == ["candidate_review", "candidate_write"])
    #expect(payload.quickLinks.first?.screen == "candidate_queue")
}
