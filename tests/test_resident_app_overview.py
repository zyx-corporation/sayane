"""Tests for resident app aggregate overview payload."""

from __future__ import annotations

from datetime import UTC, datetime

from sayane.app import build_app_overview, build_resident_runtime
from sayane.core.candidate import (
    CaptureMetadata,
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
)
from sayane.core.review_decision import ReviewDecision
from sayane.storage.repositories import build_test_repository_bundle


def test_app_overview_aggregates_runtime_review_mcp_and_daemon(tmp_path) -> None:
    runtime = build_resident_runtime(home=tmp_path / "sayane")

    payload = build_app_overview(runtime)

    assert payload["kind"] == "resident_app_overview"
    assert payload["runtime"]["profile_id"] == "default"
    assert payload["review_queue"]["kind"] == "resident_review_queue"
    assert payload["review_queue"]["repository_available"] is False
    assert payload["summary"]["reviewable_count"] == 0
    assert payload["review_summary"]["top_items"] == []
    assert payload["mcp_preview"]["preview"]["kind"] == "resident_mcp_preview"
    assert payload["mcp_preview"]["repository_available"] is False
    assert payload["mcp_summary"]["approved_context_count"] == 0
    assert payload["daemon_overview"]["kind"] == "resident_daemon_overview_preview"
    assert payload["daemon_summary"]["state"] == "stopped"
    assert payload["operator_packaging"]["kind"] == "resident_daemon_packaging_status"
    assert payload["service_control_boundary"]["kind"] == "resident_daemon_service_control_boundary"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert payload["supervision_status"]["kind"] == "resident_daemon_supervision_status"
    assert payload["recovery_consent_status"]["kind"] == "resident_daemon_recovery_consent_status"
    if payload["summary"]["service_target_platform"] == "macos":
        assert payload["daemon_overview"]["launchagent_status"]["kind"] == "resident_daemon_launchagent_status"
    assert payload["summary"]["packaging_model"] == "cli_first_local_bridge"
    assert payload["summary"]["control_plane_status"] == "cli_control_supported_local_mvp"
    assert payload["summary"]["service_target_platform"] in {"macos", "linux", "windows", "other"}
    assert payload["summary"]["supervision_mode"] == "passive_local_observation_with_cli_recovery"
    assert payload["summary"]["consent_model"] == "explicit_cli_confirmation_for_mutation"
    assert payload["vault_status"]["kind"] == "resident_app_vault_status"
    assert payload["vault_session_status"]["kind"] == "resident_app_vault_session_status"
    assert payload["summary"]["vault_status"] == "unavailable"
    assert payload["summary"]["vault_backend"] == "legacy_process_local"
    assert payload["summary"]["vault_session_count"] == 0


def test_app_overview_exposes_ui_friendly_summary_with_repositories(tmp_path) -> None:
    bundle = build_test_repository_bundle(profile_id="default")
    candidate = CandidateUpdate(
        id="c-review-1",
        status="pending",
        target_profile_id="default",
        content="approved context",
        display_summary="summary for review",
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
        ),
        source=CandidateSource(
            type="clipboard",
            captured_at=datetime.now(UTC),
        ),
        proposal=CandidateProposal(
            section="important_terms",
            add=["Sayane"],
            summary="summary for review",
        ),
    )
    bundle.candidates.save(candidate)
    bundle.review_decisions.append(
        ReviewDecision(
            candidate_id="c-approved-1",
            decision="approve",
            reason="accepted",
            applied_value="approved value",
            original_section="important_terms",
        )
    )
    runtime = build_resident_runtime(
        home=tmp_path / "sayane",
        repositories=bundle,
    )

    payload = build_app_overview(runtime)

    assert payload["summary"]["repository_available"] is True
    assert payload["summary"]["reviewable_count"] == 1
    assert payload["review_summary"]["top_items"][0]["candidate_id"] == "c-review-1"
    assert payload["mcp_summary"]["approved_context_count"] == 1
    assert payload["mcp_summary"]["top_approved_candidate_ids"] == ["c-approved-1"]
    assert payload["daemon_summary"]["next_action_count"] >= 1
    assert payload["summary"]["service_integration_status"] in {
        "contract_only",
        "macos_launchagent_preview_apply_control",
        "linux_systemd_user_preview_apply_unit_write",
    }
    assert payload["service_control_boundary"]["service_plane"]["status"] in {
        "contract_only",
        "macos_explicit_cli_only",
        "mvp_macos_launchagent_preview_apply_cli_only",
        "post_mvp_macos_launchagent_preview_apply_cli_only",
        "post_mvp_linux_systemd_user_preview_apply_cli_only",
    }
    assert payload["supervision_status"]["background_surfaces"]["status"] == "not_supported"
    assert payload["recovery_consent_status"]["mutating_recovery_actions"][0]["consent_required"] is True
    assert payload["vault_status"]["status"] == "unavailable"
    assert payload["vault_session_status"]["active_session_count"] == 0


def test_app_overview_exposes_linux_systemd_payloads(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("sayane.app.ui.sys.platform", "linux")
    monkeypatch.setattr("sayane.app.daemon_packaging_status.sys.platform", "linux")
    monkeypatch.setattr("sayane.app.daemon_service_control_boundary.sys.platform", "linux")
    monkeypatch.setattr("sayane.app.daemon_service_targets_status.sys.platform", "linux")
    monkeypatch.setattr("sayane.app.daemon_systemd_user.sys.platform", "linux")

    runtime = build_resident_runtime(home=tmp_path / "sayane")

    payload = build_app_overview(runtime)

    assert payload["summary"]["service_target_platform"] == "linux"
    assert payload["summary"]["service_integration_status"] == "linux_systemd_user_preview_apply_unit_write"
    assert payload["daemon_overview"]["launchagent_preview"] is None
    assert payload["daemon_overview"]["launchagent_status"] is None
    assert payload["daemon_overview"]["systemd_user_preview"]["kind"] == "resident_daemon_systemd_user_plan"
    assert payload["daemon_overview"]["systemd_user_status"]["kind"] == "resident_daemon_systemd_user_status"
    assert payload["daemon_overview"]["systemd_user_status"]["active_status"] in {
        "unknown",
        "inactive",
        "systemctl_not_available",
    }
    assert any(
        item["command"] == "sayane app daemon-systemd-user-preview --json"
        for item in payload["daemon_overview"]["next_actions"]
    )


def test_app_overview_degrades_when_vault_runtime_has_no_read_session(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAYANE_APP_VAULT_MODE", "development")
    monkeypatch.setenv("SAYANE_VAULT_PASSPHRASE", "dev-passphrase")
    runtime = build_resident_runtime(home=tmp_path / "sayane")

    payload = build_app_overview(runtime)

    assert payload["runtime"]["has_repositories"] is True
    assert payload["summary"]["repository_available"] is False
    assert payload["review_queue"]["repository_available"] is False
    assert payload["mcp_preview"]["repository_available"] is False
