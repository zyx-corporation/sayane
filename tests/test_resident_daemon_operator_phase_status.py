"""Tests for aggregated resident daemon operator phase status."""

from __future__ import annotations

import sys
from pathlib import Path

from sayane.app import build_daemon_operator_phase_status


def test_daemon_operator_phase_status_aggregates_post_app_workstreams(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_operator_phase_status(
        runtime_root,
        host="localhost",
        port=39000,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_operator_phase_status"
    assert payload["phase"] == "operator_packaging_and_supervision"
    assert payload["phase_status"] == "mvp_operator_boundary_closed"
    assert payload["phase_readiness"] == "ready_for_mvp_release_closure"
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["current_supported_operator_path"]["startup_command_text"] == (
        "./scripts/run-macos-app-preview.sh"
        if sys.platform == "darwin"
        else "sayane serve --host localhost --port 39000"
    )
    assert payload["current_supported_operator_path"]["primary_operator_ui"] in {
        "native_macos_app_primary",
        "local_bridge_shell_primary",
    }
    assert payload["current_supported_operator_path"]["debug_operator_ui"] == "bridge_hosted_debug_shell"
    assert payload["current_supported_operator_path"]["recommended_launcher"]
    assert payload["workstreams"][0]["name"] == "packaging_model_decision"
    assert payload["workstreams"][0]["status"] == "closed_for_mvp"
    assert payload["workstreams"][0]["candidate_models"][0]["model"] == "cli_first_local_bridge"
    assert payload["workstreams"][0]["candidate_models"][-1]["model"] == "service_first_resident_runtime"
    assert payload["workstreams"][1]["name"] == "service_integration_line"
    assert payload["workstreams"][1]["policy_gates"]["platform_policy_required"] is True
    assert payload["workstreams"][1]["lifecycle_operations"][0]["operation"] == "install"
    assert payload["workstreams"][1]["lifecycle_operations"][-1]["operation"] == "update"
    assert payload["workstreams"][2]["name"] == "supervision_ux_line"
    assert payload["workstreams"][2]["background_candidates"][0]["surface"] == "tray_supervision"
    assert payload["workstreams"][3]["name"] == "recovery_and_consent_line"
    assert payload["phase_closure_checklist"][0]["item"] == "supported_packaging_model_finalized"
    assert payload["phase_closure_checklist"][1]["item"] == "service_lifecycle_implementation_closed"
    assert payload["blocking_reasons"] == []
    assert payload["decision_assist"][0]["topic"] == "packaging_model_decision"
    assert payload["decision_assist"][0]["command"] == (
        "./scripts/run-macos-app-preview.sh"
        if sys.platform == "darwin"
        else "sayane app daemon-packaging-status --json"
    )
    assert "sayane app daemon-operator-phase-status --json" in payload["read_surfaces"]
    assert payload["closure_evidence"][0]["surface"] == "operator_phase_status"
    assert payload["closure_evidence"][0]["command"] == "sayane app daemon-operator-phase-status --json"
    assert payload["packaging_status"]["kind"] == "resident_daemon_packaging_status"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert payload["service_control_boundary"]["kind"] == "resident_daemon_service_control_boundary"
    assert payload["supervision_status"]["kind"] == "resident_daemon_supervision_status"
    assert payload["recovery_consent_status"]["kind"] == "resident_daemon_recovery_consent_status"
