"""Tests for resident app screen state builders."""

from sayane.app import (
    build_candidate_detail_screen_state,
    build_candidate_queue_screen_state,
    build_daemon_panel_screen_state,
    build_home_screen_state,
)


def test_build_home_screen_state_exposes_cards_and_links() -> None:
    payload = build_home_screen_state(
        {
            "summary": {
                "repository_available": True,
                "reviewable_count": 2,
                "approved_context_count": 1,
                "blocked_context_count": 1,
                "daemon_state": "stopped",
                "next_action_count": 2,
            },
            "review_summary": {"top_items": [{"candidate_id": "c1"}]},
            "daemon_summary": {"top_next_actions": [{"command": "x"}]},
        }
    )

    assert payload["kind"] == "resident_app_home_screen_state"
    assert payload["summary_cards"][0]["key"] == "repository"
    assert payload["top_review_items"][0]["candidate_id"] == "c1"
    assert payload["quick_links"][0]["screen"] == "candidate_queue"


def test_build_candidate_queue_screen_state_preserves_counts() -> None:
    payload = build_candidate_queue_screen_state(
        {
            "reviewable_count": 2,
            "status_counts": {"pending": 1, "evaluated": 1},
            "top_sections": [{"section": "knowledge.concepts", "count": 2}],
            "items": [{"id": "c1"}],
        }
    )

    assert payload["kind"] == "resident_app_candidate_queue_screen_state"
    assert payload["status_counts"]["pending"] == 1
    assert payload["default_sort"] == "captured_at_desc"


def test_build_candidate_detail_screen_state_exposes_actions() -> None:
    payload = build_candidate_detail_screen_state(
        {
            "ui_summary": {"status": "evaluated"},
            "allowed_actions": {"approve": True},
            "proposal": {"section": "knowledge.concepts"},
            "evaluation": {"level": 1},
            "content": "hello",
        }
    )

    assert payload["kind"] == "resident_app_candidate_detail_screen_state"
    assert payload["allowed_actions"]["approve"] is True
    assert payload["diff_available"] is True


def test_build_daemon_panel_screen_state_exposes_cards_and_previews() -> None:
    payload = build_daemon_panel_screen_state(
        {
            "status": {"state": "stopped", "is_running_daemon": False, "runtime_initialized": False},
            "readiness": {"readiness_status": "review_required"},
            "next_actions": [{"command": "sayane app daemon-status --json"}],
            "runtime_init": {"kind": "resident_daemon_runtime_init_plan"},
            "cleanup_preview": {"kind": "resident_daemon_cleanup_apply_preview"},
            "repair_preview": {"kind": "resident_daemon_repair_apply_preview"},
            "packaging_status": {
                "kind": "resident_daemon_packaging_status",
                "packaging_model": "cli_first_local_bridge",
                "supervision_model": "manual_cli_with_bridge_delegation",
                "phase_status": "next_up_after_proof_phase",
            },
            "service_control_boundary": {
                "kind": "resident_daemon_service_control_boundary",
                "control_plane": {
                    "allowed_commands": [{"command": "sayane app daemon-start --json"}],
                },
                "service_plane": {
                    "status": "macos_explicit_cli_only",
                    "allowed_commands": [{"command": "sayane app daemon-launchagent-bootstrap --json"}],
                    "deferred_commands": ["daemon-service-install"],
                },
            },
            "service_targets_status": {"kind": "resident_daemon_service_targets_status"},
            "supervision_status": {
                "kind": "resident_daemon_supervision_status",
                "supervision_mode": "passive_local_observation_with_cli_recovery",
                "active_supervision": {"allowed_actions": ["sayane app daemon-start --json"]},
            },
            "recovery_consent_status": {
                "kind": "resident_daemon_recovery_consent_status",
                "consent_model": "explicit_cli_confirmation_for_mutation",
                "recommended_recovery_flow": ["inspect current status and proof-oriented diagnostics"],
            },
            "operator_phase_status": {
                "phase": "operator_packaging_and_supervision",
                "phase_status": "mvp_operator_boundary_closed",
                "phase_readiness": "ready_for_mvp_release_closure",
                "blocking_reasons": [],
                "current_supported_operator_path": {
                    "startup_command_text": "sayane serve --host 127.0.0.1 --port 38741",
                    "primary_operator_ui": "native_macos_app_primary",
                    "debug_operator_ui": "bridge_hosted_debug_shell",
                    "recommended_launcher": "./scripts/run-macos-app-preview.sh",
                    "bootstrap_ui": "http://127.0.0.1:38741/app/ui",
                    "local_only": True,
                    "notes": ["current supported operator path remains local Python CLI plus Local Bridge"],
                },
                "workstreams": [
                    {
                        "name": "packaging_model_decision",
                        "status": "closed_for_mvp",
                        "current_state": "cli_first_local_bridge",
                    }
                ],
                "recommended_implementation_order": [],
                "decision_assist": [
                    {
                        "topic": "packaging_model_decision",
                        "summary": "keep current line explicit",
                        "command": "sayane app daemon-packaging-status --json",
                    }
                ],
                "read_surfaces": ["sayane app daemon-operator-phase-status --json"],
                "closure_evidence": [
                    {
                        "surface": "operator_phase_status",
                        "command": "sayane app daemon-operator-phase-status --json",
                        "confirms": "phase readiness",
                    }
                ],
                "exit_criteria": ["supported operator packaging model is explicit"],
                "not_in_scope": ["direct profile patch UI"],
                "phase_closure_checklist": [
                    {"item": "supported_packaging_model_finalized", "status": "complete"},
                ],
            },
            "launchagent_preview": {"kind": "resident_daemon_launchagent_plan"},
            "launchagent_status": {"kind": "resident_daemon_launchagent_status", "loaded_status": "loaded"},
        }
    )

    assert payload["kind"] == "resident_app_daemon_panel_screen_state"
    assert payload["summary_cards"][0]["key"] == "state"
    assert payload["next_actions"][0]["command"] == "sayane app daemon-status --json"
    assert payload["operator_panels"][0]["panel"] == "packaging_status"
    assert payload["operator_panels"][1]["deferred_commands"] == ["daemon-service-install"]
    assert payload["service_target_summary"]["targets"] == []
    assert payload["launchagent_summary"]["status_available"] is True
    assert payload["launchagent_summary"]["loaded_status"] == "loaded"
    assert payload["operator_phase_summary"]["phase_readiness"] == "ready_for_mvp_release_closure"
    assert payload["operator_phase_summary"]["blocking_reasons"] == []
    assert payload["operator_phase_details"]["current_supported_operator_path"]["local_only"] is True
    assert payload["operator_phase_details"]["current_supported_operator_path"]["primary_operator_ui"] == "native_macos_app_primary"
    assert payload["operator_phase_details"]["workstreams"][0]["detail"] == "cli_first_local_bridge"
    assert payload["operator_phase_details"]["decision_assist"][0]["topic"] == "packaging_model_decision"
    assert payload["operator_phase_details"]["read_surfaces"] == ["sayane app daemon-operator-phase-status --json"]
    assert payload["operator_phase_details"]["closure_evidence"][0]["surface"] == "operator_phase_status"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert payload["operator_phase_status"]["phase"] == "operator_packaging_and_supervision"
    assert payload["launchagent_preview"]["kind"] == "resident_daemon_launchagent_plan"
    assert payload["launchagent_status"]["kind"] == "resident_daemon_launchagent_status"
