"""CLI tests for LaunchAgent preview/apply commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.app import build_launchagent_plan
from sayane.cli.main import app

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


def test_daemon_launchagent_preview_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-launchagent-preview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_launchagent_plan"


def test_daemon_launchagent_apply_json(isolated_home: Path) -> None:
    plan = build_launchagent_plan(isolated_home / ".sayane" / "run", sayane_home=isolated_home / ".sayane")
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-launchagent-apply",
            "--operation-id",
            plan.operation_id,
            "--confirm-operation-id",
            plan.operation_id,
            "--confirm-preview-hash",
            plan.preview_hash(),
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["kind"] == "resident_daemon_launchagent_receipt"


def test_daemon_launchagent_bootstrap_json(isolated_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sayane.app.daemon_launchagent.sys.platform", "darwin")
    plan = build_launchagent_plan(isolated_home / ".sayane" / "run", sayane_home=isolated_home / ".sayane")
    plan.plist_path.parent.mkdir(parents=True, exist_ok=True)
    plan.plist_path.write_text(plan.plist_xml(), encoding="utf-8")

    def _fake_run_launchagent_command(plan, *, action):
        return {
            "kind": "resident_daemon_launchagent_control_receipt",
            "operation_id": plan.operation_id,
            "preview_hash": plan.preview_hash(),
            "label": "com.sayane.resident.bridge",
            "action": action,
            "platform": "macos",
            "plist_path": str(plan.plist_path),
            "command": ["launchctl", action],
            "result": "completed",
            "applied": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "sayane.cli.commands.app_daemon_launchagent.run_launchagent_command",
        _fake_run_launchagent_command,
    )

    result = runner.invoke(app, ["app", "daemon-launchagent-bootstrap", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_launchagent_control_receipt"
    assert payload["action"] == "bootstrap"


def test_daemon_launchagent_bootstrap_json_returns_error_payload(
    isolated_home: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fake_control_error(plan, *, action):
        from sayane.app import ResidentDaemonLaunchAgentControlError

        raise ResidentDaemonLaunchAgentControlError(
            "boom",
            payload={
                "kind": "resident_daemon_launchagent_control_receipt",
                "action": action,
                "result": "aborted",
                "applied": False,
                "failure_mode": "plist_missing",
            },
        )

    monkeypatch.setattr(
        "sayane.cli.commands.app_daemon_launchagent.run_launchagent_command",
        _fake_control_error,
    )

    result = runner.invoke(app, ["app", "daemon-launchagent-bootstrap", "--json"])

    assert result.exit_code == 1
    assert json.loads(result.stdout)["failure_mode"] == "plist_missing"


def test_daemon_launchagent_status_json(isolated_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sayane.app.daemon_launchagent.sys.platform", "darwin")

    def _fake_build_launchagent_status(plan):
        return {
            "kind": "resident_daemon_launchagent_status",
            "label": "com.sayane.resident.bridge",
            "plist_path": str(plan.plist_path),
            "plist_exists": True,
            "loaded": False,
            "loaded_status": "not_loaded",
            "service_manager": "launchd",
        }

    monkeypatch.setattr(
        "sayane.cli.commands.app_daemon_launchagent.build_launchagent_status",
        _fake_build_launchagent_status,
    )

    result = runner.invoke(app, ["app", "daemon-launchagent-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_launchagent_status"
    assert payload["loaded_status"] == "not_loaded"
