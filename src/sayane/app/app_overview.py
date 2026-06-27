"""Resident app-facing aggregate overview payload."""

from __future__ import annotations

from typing import Any

from sayane.app.daemon_packaging_status import build_daemon_packaging_status
from sayane.app.daemon_recovery_consent_status import build_daemon_recovery_consent_status
from sayane.app.daemon_service_control_boundary import build_daemon_service_control_boundary
from sayane.app.daemon_service_targets_status import build_daemon_service_targets_status
from sayane.app.daemon_supervision_status import build_daemon_supervision_status
from sayane.app.runtime import ResidentRuntime
from sayane.app.vault_session_status import build_app_vault_session_status
from sayane.app.vault_status import build_app_vault_status
from sayane.app.ui import (
    build_daemon_overview_preview,
    build_mcp_preview,
    build_review_queue,
)


def build_app_overview(runtime: ResidentRuntime) -> dict[str, Any]:
    """Build an aggregate resident app overview for future UI surfaces."""
    describe = runtime.describe()
    if runtime.service.repositories is None:
        review_queue = {
            "profile_id": runtime.service.profile_id,
            "kind": "resident_review_queue",
            "is_review_surface": True,
            "is_mcp_context": False,
            "items": [],
            "repository_available": False,
        }
        mcp_preview = {
            "profile_id": runtime.service.profile_id,
            "mode": "full",
            "is_derived_context": True,
            "is_canonical_profile": False,
            "included_approved_candidates": [],
            "blocked_candidates": [],
            "repository_available": False,
            "preview": {
                "kind": "resident_mcp_preview",
                "is_preview": True,
                "is_derived_context": True,
                "is_canonical_profile": False,
            },
        }
    else:
        review_queue = build_review_queue(
            runtime.service.repositories,
            capability=runtime.capabilities["ui"],
        )
        review_queue["repository_available"] = True
        mcp_preview = build_mcp_preview(
            runtime.service.repositories,
            capability=runtime.capabilities["mcp"],
            mode="full",
        )
        mcp_preview["repository_available"] = True

    daemon_overview = build_daemon_overview_preview(
        runtime.bridge_config.home / "run",
        capability=runtime.capabilities["ui"],
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    )
    operator_packaging = build_daemon_packaging_status(
        runtime.bridge_config.home / "run",
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    ).public_metadata()
    service_control_boundary = build_daemon_service_control_boundary(
        runtime.bridge_config.home / "run",
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    ).public_metadata()
    service_targets_status = build_daemon_service_targets_status(
        runtime.bridge_config.home / "run",
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    ).public_metadata()
    supervision_status = build_daemon_supervision_status(
        runtime.bridge_config.home / "run",
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    ).public_metadata()
    recovery_consent_status = build_daemon_recovery_consent_status(
        runtime.bridge_config.home / "run",
        host=runtime.bridge_config.host,
        port=runtime.bridge_config.port,
    ).public_metadata()
    vault_status = build_app_vault_status(runtime)
    vault_session_status = build_app_vault_session_status(runtime)
    review_summary = _build_review_summary(review_queue)
    mcp_summary = _build_mcp_summary(mcp_preview)
    daemon_summary = _build_daemon_summary(daemon_overview)
    return {
        "kind": "resident_app_overview",
        "profile_id": runtime.service.profile_id,
        "runtime": describe,
        "summary": {
            "repository_available": review_queue["repository_available"],
            "reviewable_count": review_summary["reviewable_count"],
            "approved_context_count": mcp_summary["approved_context_count"],
            "blocked_context_count": mcp_summary["blocked_context_count"],
            "daemon_state": daemon_summary["state"],
            "readiness_status": daemon_summary["readiness_status"],
            "next_action_count": daemon_summary["next_action_count"],
            "packaging_model": operator_packaging["packaging_model"],
            "service_integration_status": operator_packaging["service_integration"]["status"],
            "control_plane_status": service_control_boundary["control_plane"]["status"],
            "service_target_platform": service_targets_status["current_platform"],
            "supervision_mode": supervision_status["supervision_mode"],
            "consent_model": recovery_consent_status["consent_model"],
            "vault_status": vault_status["status"],
            "vault_backend": vault_status["backend"],
            "vault_assurance": vault_status["keychain_assurance"],
            "vault_session_count": vault_session_status["active_session_count"],
        },
        "review_summary": review_summary,
        "mcp_summary": mcp_summary,
        "daemon_summary": daemon_summary,
        "operator_packaging": operator_packaging,
        "service_control_boundary": service_control_boundary,
        "service_targets_status": service_targets_status,
        "supervision_status": supervision_status,
        "recovery_consent_status": recovery_consent_status,
        "vault_status": vault_status,
        "vault_session_status": vault_session_status,
        "review_queue": review_queue,
        "mcp_preview": mcp_preview,
        "daemon_overview": daemon_overview,
    }


def _build_review_summary(review_queue: dict[str, Any]) -> dict[str, Any]:
    items = review_queue.get("items", [])
    top_items = [
        {
            "candidate_id": item["candidate_id"],
            "status": item["status"],
            "proposal_section": item["proposal_section"],
            "display_summary": item["display_summary"],
            "requires_review": item["requires_review"],
        }
        for item in items[:3]
    ]
    return {
        "reviewable_count": len(items),
        "top_items": top_items,
    }


def _build_mcp_summary(mcp_preview: dict[str, Any]) -> dict[str, Any]:
    approved = mcp_preview.get("included_approved_candidates", [])
    blocked = mcp_preview.get("blocked_candidates", [])
    return {
        "approved_context_count": len(approved),
        "blocked_context_count": len(blocked),
        "top_approved_candidate_ids": [
            entry["candidate_id"] for entry in approved[:3] if "candidate_id" in entry
        ],
    }


def _build_daemon_summary(daemon_overview: dict[str, Any]) -> dict[str, Any]:
    status = daemon_overview["status"]
    readiness = daemon_overview["readiness"]
    next_actions = daemon_overview.get("next_actions", [])
    return {
        "state": status["state"],
        "is_running_daemon": status["is_running_daemon"],
        "runtime_initialized": status["runtime_initialized"],
        "readiness_status": readiness["readiness_status"],
        "api_readiness_status": readiness["api_readiness_status"],
        "next_action_count": len(next_actions),
        "top_next_actions": next_actions[:3],
    }
