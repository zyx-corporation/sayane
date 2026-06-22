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
            "service_targets_status": {"kind": "resident_daemon_service_targets_status"},
            "launchagent_preview": {"kind": "resident_daemon_launchagent_plan"},
            "launchagent_status": {"kind": "resident_daemon_launchagent_status"},
        }
    )

    assert payload["kind"] == "resident_app_daemon_panel_screen_state"
    assert payload["summary_cards"][0]["key"] == "state"
    assert payload["next_actions"][0]["command"] == "sayane app daemon-status --json"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert payload["launchagent_preview"]["kind"] == "resident_daemon_launchagent_plan"
    assert payload["launchagent_status"]["kind"] == "resident_daemon_launchagent_status"
