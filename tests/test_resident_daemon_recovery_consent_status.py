"""Tests for resident daemon recovery and consent status."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_recovery_consent_status


def test_daemon_recovery_consent_status_exposes_cli_first_recovery_flow(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_recovery_consent_status(
        runtime_root,
        host="localhost",
        port=39000,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_recovery_consent_status"
    assert payload["consent_model"] == "explicit_cli_confirmation_for_mutation"
    assert payload["recovery_model"] == "diagnose_then_operator_review_then_cli_action"
    assert payload["mutating_recovery_actions"][0]["consent_required"] is True
    assert payload["mutating_recovery_actions"][0]["scope"] == "runtime initialization artifacts"
    assert payload["control_recovery_actions"][0]["notes"]
    assert "sayane app daemon-proof-diagnostics --operation-class bridge_health --json" in payload[
        "non_mutating_diagnostics"
    ]
