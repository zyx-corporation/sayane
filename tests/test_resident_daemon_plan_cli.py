"""Tests for resident daemon operation plan CLI commands (#189)."""

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


def test_daemon_start_plan_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-start-plan", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_operation_plan"
    assert payload["operation"] == "start"
    assert payload["target_state"] == "starting"
    assert payload["transition_allowed"] is True
    assert payload["plan_only"] is True
    assert payload["would_start_daemon"] is False
    assert payload["would_stop_daemon"] is False
    assert payload["would_restart_daemon"] is False
    assert payload["planned_sequence"] == ["start"]
    assert payload["current_serve_path"] == "delegate_to_sayane_serve"


def test_daemon_stop_plan_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-stop-plan", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_operation_plan"
    assert payload["operation"] == "stop"
    assert payload["target_state"] == "stopping"
    assert payload["transition_allowed"] is False
    assert payload["plan_only"] is True
    assert payload["would_start_daemon"] is False
    assert payload["would_stop_daemon"] is False
    assert payload["would_restart_daemon"] is False
    assert payload["planned_sequence"] == ["stop"]


def test_daemon_restart_plan_json(isolated_home: Path) -> None:
    result = runner.invoke(
        app,
        ["app", "daemon-restart-plan", "--host", "localhost", "--port", "39000", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_operation_plan"
    assert payload["operation"] == "restart"
    assert payload["target_state"] == "starting"
    assert payload["transition_allowed"] is True
    assert payload["host"] == "localhost"
    assert payload["port"] == 39000
    assert payload["would_restart_daemon"] is False
    assert payload["planned_sequence"] == ["stop-if-running", "start"]
    assert payload["bridge_command"] == [
        "sayane",
        "serve",
        "--host",
        "localhost",
        "--port",
        "39000",
    ]


def test_daemon_operation_plans_reject_non_localhost(isolated_home: Path) -> None:
    commands = ["daemon-start-plan", "daemon-stop-plan", "daemon-restart-plan"]

    for command in commands:
        result = runner.invoke(app, ["app", command, "--host", "0.0.0.0"])
        assert result.exit_code != 0
        assert "localhost" in (result.stdout + result.stderr + str(result.exception)).lower()
