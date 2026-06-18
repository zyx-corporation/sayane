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


def test_daemon_preflight_json_can_include_schema_only_event_record() -> None:
    result = runner.invoke(
        app,
        ["app", "daemon-preflight", "--json", "--include-event-record"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_preflight_report"
    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["category"] == "preview"
    assert payload["event_record"]["surface"] == "daemon-preflight"
    assert payload["event_record"]["result"] == "requires_review"
    assert payload["event_record"]["persisted"] is False
    assert payload["event_record"]["mutates_filesystem"] is False
    assert payload["event_record"]["controls_process"] is False
    assert payload["event_record"]["exposes_ipc"] is False
    assert payload["event_record"]["integrates_os_service"] is False


def test_daemon_preflight_text_can_include_event_record_summary() -> None:
    result = runner.invoke(
        app,
        ["app", "daemon-preflight", "--include-event-record"],
    )

    assert result.exit_code == 0
    assert "event_record.kind: resident_daemon_event_record" in result.stdout
    assert "event_record.result: requires_review" in result.stdout
