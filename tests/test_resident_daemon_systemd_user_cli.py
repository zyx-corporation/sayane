"""CLI tests for Linux systemd --user preview/apply commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.app import build_systemd_user_plan
from sayane.cli.main import app

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


def test_daemon_systemd_user_preview_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-systemd-user-preview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_systemd_user_plan"


def test_daemon_systemd_user_apply_json(isolated_home: Path) -> None:
    plan = build_systemd_user_plan(isolated_home / ".sayane" / "run", sayane_home=isolated_home / ".sayane")
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-systemd-user-apply",
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
    assert json.loads(result.stdout)["kind"] == "resident_daemon_systemd_user_receipt"


def test_daemon_systemd_user_status_json(isolated_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sayane.app.daemon_systemd_user.sys.platform", "linux")

    def _fake_build_systemd_user_status(plan):
        return {
            "kind": "resident_daemon_systemd_user_status",
            "unit_name": "sayane-resident-bridge.service",
            "unit_path": str(plan.unit_path),
            "unit_exists": True,
            "active": False,
            "enabled": False,
            "active_status": "inactive",
            "enabled_status": "disabled",
            "service_manager": "systemd --user",
        }

    monkeypatch.setattr(
        "sayane.cli.commands.app_daemon_systemd_user.build_systemd_user_status",
        _fake_build_systemd_user_status,
    )

    result = runner.invoke(app, ["app", "daemon-systemd-user-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_systemd_user_status"
    assert payload["enabled_status"] == "disabled"


def test_daemon_systemd_user_enable_now_json(isolated_home: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def _fake_run_systemd_user_command(plan, *, action):
        return {
            "kind": "resident_daemon_systemd_user_control_receipt",
            "operation_id": plan.operation_id,
            "preview_hash": plan.preview_hash(),
            "unit_name": "sayane-resident-bridge.service",
            "action": action,
            "platform": "linux",
            "unit_path": str(plan.unit_path),
            "command": ["systemctl", "--user", "enable", "--now", "sayane-resident-bridge.service"],
            "result": "completed",
            "applied": True,
            "returncode": 0,
            "stdout": "",
            "stderr": "",
        }

    monkeypatch.setattr(
        "sayane.cli.commands.app_daemon_systemd_user.run_systemd_user_command",
        _fake_run_systemd_user_command,
    )

    result = runner.invoke(app, ["app", "daemon-systemd-user-enable-now", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_systemd_user_control_receipt"
    assert payload["action"] == "enable_now"
