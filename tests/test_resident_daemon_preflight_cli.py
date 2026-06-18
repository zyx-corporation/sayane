"""Tests for resident daemon preflight CLI."""

from __future__ import annotations

import json

from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


def test_daemon_preflight_json_reports_schema_only_gate_status() -> None:
    result = runner.invoke(app, ["app", "daemon-preflight", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_preflight_report"
    assert payload["target_scope"] == "resident_daemon_implementation_gate"
    assert payload["status"] == "review_required"
    assert payload["mutates_filesystem"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["exposes_ipc"] is False
    assert payload["integrates_os_service"] is False
    assert len(payload["items"]) == 7


def test_daemon_preflight_text_output_is_non_mutating_summary() -> None:
    result = runner.invoke(app, ["app", "daemon-preflight"])

    assert result.exit_code == 0
    assert "kind: resident_daemon_preflight_report" in result.stdout
    assert "status: review_required" in result.stdout
    assert "mutates_filesystem: False" in result.stdout
    assert "probes_process: False" in result.stdout
    assert "controls_process: False" in result.stdout
    assert "exposes_ipc: False" in result.stdout
    assert "integrates_os_service: False" in result.stdout
