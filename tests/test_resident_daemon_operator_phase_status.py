"""Tests for aggregated resident daemon operator phase status."""

from __future__ import annotations

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
    assert payload["phase_status"] == "baseline_contracts_implemented_next_phase_open"
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["current_supported_operator_path"]["startup_command_text"] == (
        "sayane serve --host localhost --port 39000"
    )
    assert payload["workstreams"][0]["name"] == "packaging_model_decision"
    assert payload["workstreams"][1]["name"] == "service_integration_line"
    assert payload["workstreams"][1]["lifecycle_operations"][0]["operation"] == "install"
    assert payload["workstreams"][1]["lifecycle_operations"][-1]["operation"] == "update"
    assert payload["workstreams"][2]["name"] == "supervision_ux_line"
    assert payload["workstreams"][3]["name"] == "recovery_and_consent_line"
    assert "sayane app daemon-operator-phase-status --json" in payload["read_surfaces"]
    assert payload["packaging_status"]["kind"] == "resident_daemon_packaging_status"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert payload["service_control_boundary"]["kind"] == "resident_daemon_service_control_boundary"
    assert payload["supervision_status"]["kind"] == "resident_daemon_supervision_status"
    assert payload["recovery_consent_status"]["kind"] == "resident_daemon_recovery_consent_status"
