"""Framework-neutral screen state builders for resident app surfaces."""

from __future__ import annotations

from typing import Any


def build_home_screen_state(overview: dict[str, Any]) -> dict[str, Any]:
    """Build a GUI-oriented home screen state from app overview."""
    summary = overview.get("summary", {})
    review_summary = overview.get("review_summary", {})
    daemon_summary = overview.get("daemon_summary", {})
    return {
        "kind": "resident_app_home_screen_state",
        "summary_cards": [
            {"key": "repository", "value": summary.get("repository_available")},
            {"key": "reviewable", "value": summary.get("reviewable_count")},
            {"key": "approved_context", "value": summary.get("approved_context_count")},
            {"key": "blocked_context", "value": summary.get("blocked_context_count")},
            {"key": "daemon_state", "value": summary.get("daemon_state")},
            {"key": "next_actions", "value": summary.get("next_action_count")},
        ],
        "top_review_items": review_summary.get("top_items", []),
        "top_daemon_actions": daemon_summary.get("top_next_actions", []),
        "quick_links": [
            {"screen": "candidate_queue", "path": "/app/candidates"},
            {"screen": "daemon_panel", "path": "/app/daemon-overview"},
        ],
    }


def build_candidate_queue_screen_state(queue_payload: dict[str, Any]) -> dict[str, Any]:
    """Build a GUI-oriented queue screen state."""
    return {
        "kind": "resident_app_candidate_queue_screen_state",
        "reviewable_count": queue_payload.get("reviewable_count", 0),
        "status_counts": queue_payload.get("status_counts", {}),
        "top_sections": queue_payload.get("top_sections", []),
        "items": queue_payload.get("items", []),
        "default_sort": "captured_at_desc",
    }


def build_candidate_detail_screen_state(
    detail_payload: dict[str, Any],
    *,
    diff_available: bool = True,
) -> dict[str, Any]:
    """Build a GUI-oriented detail screen state."""
    return {
        "kind": "resident_app_candidate_detail_screen_state",
        "ui_summary": detail_payload.get("ui_summary", {}),
        "allowed_actions": detail_payload.get("allowed_actions", {}),
        "proposal": detail_payload.get("proposal", {}),
        "evaluation": detail_payload.get("evaluation", {}),
        "content": detail_payload.get("content"),
        "diff_available": diff_available,
    }


def build_daemon_panel_screen_state(daemon_payload: dict[str, Any]) -> dict[str, Any]:
    """Build a GUI-oriented daemon panel state."""
    status = daemon_payload.get("status", {})
    readiness = daemon_payload.get("readiness", {})
    return {
        "kind": "resident_app_daemon_panel_screen_state",
        "summary_cards": [
            {"key": "state", "value": status.get("state")},
            {"key": "is_running_daemon", "value": status.get("is_running_daemon")},
            {"key": "runtime_initialized", "value": status.get("runtime_initialized")},
            {"key": "readiness_status", "value": readiness.get("readiness_status")},
        ],
        "packaging_status": daemon_payload.get("packaging_status", {}),
        "service_control_boundary": daemon_payload.get("service_control_boundary", {}),
        "service_targets_status": daemon_payload.get("service_targets_status", {}),
        "supervision_status": daemon_payload.get("supervision_status", {}),
        "recovery_consent_status": daemon_payload.get("recovery_consent_status", {}),
        "launchagent_preview": daemon_payload.get("launchagent_preview"),
        "next_actions": daemon_payload.get("next_actions", []),
        "runtime_init": daemon_payload.get("runtime_init", {}),
        "cleanup_preview": daemon_payload.get("cleanup_preview", {}),
        "repair_preview": daemon_payload.get("repair_preview", {}),
    }
