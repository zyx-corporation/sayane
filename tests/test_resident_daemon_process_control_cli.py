"""CLI tests for minimal resident daemon process control."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


def test_daemon_start_json_reports_runtime_init_required(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-start", "--json"])

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["operation"] == "start"
    assert payload["failure_mode"] == "runtime_init_required"


def test_daemon_start_json_failure_can_include_event_record(isolated_home: Path) -> None:
    result = runner.invoke(
        app,
        ["app", "daemon-start", "--include-event-record", "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["category"] == "process"
    assert payload["event_record"]["result"] == "aborted"


def test_daemon_status_json_includes_runtime_root(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_lifecycle_status"
    assert payload["runtime_root"].endswith("/run")
    assert payload["pid_path"].endswith("/sayane-resident.pid")
