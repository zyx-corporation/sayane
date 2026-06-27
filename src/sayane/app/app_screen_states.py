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
    packaging_status = daemon_payload.get("packaging_status", {})
    service_control_boundary = daemon_payload.get("service_control_boundary", {})
    service_targets_status = daemon_payload.get("service_targets_status", {})
    supervision_status = daemon_payload.get("supervision_status", {})
    recovery_consent_status = daemon_payload.get("recovery_consent_status", {})
    operator_phase_status = daemon_payload.get("operator_phase_status", {})
    launchagent_preview = daemon_payload.get("launchagent_preview")
    launchagent_status = daemon_payload.get("launchagent_status")
    return {
        "kind": "resident_app_daemon_panel_screen_state",
        "summary_cards": [
            {"key": "state", "value": status.get("state")},
            {"key": "is_running_daemon", "value": status.get("is_running_daemon")},
            {"key": "runtime_initialized", "value": status.get("runtime_initialized")},
            {"key": "readiness_status", "value": readiness.get("readiness_status")},
        ],
        "operator_panels": [
            {
                "panel": "packaging_status",
                "title": "packaging_status",
                "status": packaging_status.get("packaging_model"),
                "highlights": [
                    packaging_status.get("supervision_model"),
                    packaging_status.get("phase_status"),
                ],
            },
            {
                "panel": "service_control_boundary",
                "title": "service_control_boundary",
                "status": service_control_boundary.get("service_plane", {}).get("status"),
                "commands": [
                    item.get("command")
                    for item in service_control_boundary.get("control_plane", {}).get(
                        "allowed_commands", []
                    )
                ]
                + [
                    item.get("command")
                    for item in service_control_boundary.get("service_plane", {}).get(
                        "allowed_commands", []
                    )
                ],
                "deferred_commands": service_control_boundary.get("service_plane", {}).get(
                    "deferred_commands", []
                ),
            },
            {
                "panel": "supervision_status",
                "title": "supervision_status",
                "status": supervision_status.get("supervision_mode"),
                "commands": supervision_status.get("active_supervision", {}).get(
                    "allowed_actions", []
                ),
            },
            {
                "panel": "recovery_consent_status",
                "title": "recovery_consent_status",
                "status": recovery_consent_status.get("consent_model"),
                "recommended_flow": recovery_consent_status.get("recommended_recovery_flow", []),
            },
        ],
        "service_target_summary": {
            "current_platform": service_targets_status.get("current_platform"),
            "recommended_target": service_targets_status.get("recommended_target"),
            "targets": service_targets_status.get("targets", []),
        },
        "launchagent_summary": {
            "preview_available": launchagent_preview is not None,
            "status_available": launchagent_status is not None,
            "plist_path": (launchagent_preview or {}).get("plist_path")
            or (launchagent_status or {}).get("plist_path"),
            "loaded_status": (launchagent_status or {}).get("loaded_status"),
            "launchctl_commands": (launchagent_preview or {}).get("launchctl_commands", {}),
        },
        "operator_phase_summary": {
            "phase": operator_phase_status.get("phase"),
            "phase_status": operator_phase_status.get("phase_status"),
            "phase_readiness": operator_phase_status.get("phase_readiness"),
            "blocking_reasons": operator_phase_status.get("blocking_reasons", []),
            "checklist": operator_phase_status.get("phase_closure_checklist", []),
        },
        "operator_phase_details": {
            "current_supported_operator_path": {
                "startup_command_text": operator_phase_status.get(
                    "current_supported_operator_path", {}
                ).get("startup_command_text"),
                "primary_operator_ui": operator_phase_status.get(
                    "current_supported_operator_path", {}
                ).get("primary_operator_ui"),
                "debug_operator_ui": operator_phase_status.get(
                    "current_supported_operator_path", {}
                ).get("debug_operator_ui"),
                "recommended_launcher": operator_phase_status.get(
                    "current_supported_operator_path", {}
                ).get("recommended_launcher"),
                "bootstrap_ui": operator_phase_status.get(
                    "current_supported_operator_path", {}
                ).get("bootstrap_ui"),
                "local_only": operator_phase_status.get("current_supported_operator_path", {}).get(
                    "local_only"
                ),
                "notes": operator_phase_status.get("current_supported_operator_path", {}).get(
                    "notes", []
                ),
            },
            "workstreams": [
                {
                    "name": item.get("name"),
                    "status": item.get("status"),
                    "detail": (
                        item.get("current_state")
                        or item.get("current_target")
                        or item.get("background_status")
                        or item.get("consent_model")
                    ),
                }
                for item in operator_phase_status.get("workstreams", [])
            ],
            "recommended_implementation_order": operator_phase_status.get(
                "recommended_implementation_order",
                [],
            ),
            "decision_assist": operator_phase_status.get("decision_assist", []),
            "read_surfaces": operator_phase_status.get("read_surfaces", []),
            "closure_evidence": operator_phase_status.get("closure_evidence", []),
            "exit_criteria": operator_phase_status.get("exit_criteria", []),
            "not_in_scope": operator_phase_status.get("not_in_scope", []),
        },
        "packaging_status": packaging_status,
        "service_control_boundary": service_control_boundary,
        "service_targets_status": service_targets_status,
        "supervision_status": supervision_status,
        "recovery_consent_status": recovery_consent_status,
        "operator_phase_status": operator_phase_status,
        "launchagent_preview": launchagent_preview,
        "launchagent_status": launchagent_status,
        "next_actions": daemon_payload.get("next_actions", []),
        "runtime_init": daemon_payload.get("runtime_init", {}),
        "cleanup_preview": daemon_payload.get("cleanup_preview", {}),
        "repair_preview": daemon_payload.get("repair_preview", {}),
    }
