"""Tests for Linux systemd --user preview/apply support."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonSystemdUserApplyError,
    ResidentDaemonSystemdUserControlError,
    apply_systemd_user_plan,
    build_systemd_user_plan,
    build_systemd_user_status,
    run_systemd_user_command,
)


def test_systemd_user_plan_exposes_unit_and_commands(tmp_path: Path) -> None:
    plan = build_systemd_user_plan(tmp_path / "run", host="localhost", port=39000, sayane_home=tmp_path / "home")
    payload = plan.public_metadata()

    assert payload["kind"] == "resident_daemon_systemd_user_plan"
    assert payload["service_manager"] == "systemd --user"
    assert payload["platform"] == "linux"
    assert payload["unit_name"] == "sayane-resident-bridge.service"
    assert "systemctl --user daemon-reload" == payload["systemctl_commands"]["daemon_reload"]


def test_systemd_user_apply_writes_unit_after_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan = build_systemd_user_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    receipt = apply_systemd_user_plan(
        plan,
        confirm_operation_id=plan.operation_id,
        confirm_preview_hash=plan.preview_hash(),
    )

    assert receipt["kind"] == "resident_daemon_systemd_user_receipt"
    assert Path(receipt["unit_path"]).is_file()


def test_systemd_user_apply_rejects_mismatched_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan = build_systemd_user_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    with pytest.raises(ResidentDaemonSystemdUserApplyError):
        apply_systemd_user_plan(plan, confirm_operation_id="bad", confirm_preview_hash="bad")


def test_systemd_user_status_reports_unit_presence_and_state(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_systemd_user.sys.platform", "linux")
    plan = build_systemd_user_plan(tmp_path / "run", sayane_home=tmp_path / "home")
    plan.unit_path.parent.mkdir(parents=True, exist_ok=True)
    plan.unit_path.write_text(plan.unit_text(), encoding="utf-8")

    results = iter(
        [
            subprocess.CompletedProcess(["systemctl"], 0, stdout="active\n", stderr=""),
            subprocess.CompletedProcess(["systemctl"], 0, stdout="enabled\n", stderr=""),
        ]
    )

    def _fake_run(command, *, capture_output, text, check):
        assert command[:2] == ["systemctl", "--user"]
        assert capture_output is True
        assert text is True
        assert check is False
        return next(results)

    monkeypatch.setattr("sayane.app.daemon_systemd_user.subprocess.run", _fake_run)

    payload = build_systemd_user_status(plan)

    assert payload["kind"] == "resident_daemon_systemd_user_status"
    assert payload["unit_exists"] is True
    assert payload["active"] is True
    assert payload["enabled"] is True
    assert payload["active_status"] == "active"
    assert payload["enabled_status"] == "enabled"


def test_systemd_user_control_runs_enable_now_on_linux(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_systemd_user.sys.platform", "linux")
    plan = build_systemd_user_plan(tmp_path / "run", sayane_home=tmp_path / "home")
    plan.unit_path.parent.mkdir(parents=True, exist_ok=True)
    plan.unit_path.write_text(plan.unit_text(), encoding="utf-8")

    def _fake_run(command, *, capture_output, text, check):
        assert command[:3] == ["systemctl", "--user", "enable"]
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("sayane.app.daemon_systemd_user.subprocess.run", _fake_run)

    payload = run_systemd_user_command(plan, action="enable_now")

    assert payload["kind"] == "resident_daemon_systemd_user_control_receipt"
    assert payload["action"] == "enable_now"
    assert payload["result"] == "completed"
    assert payload["applied"] is True


def test_systemd_user_control_rejects_missing_unit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_systemd_user.sys.platform", "linux")
    plan = build_systemd_user_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    with pytest.raises(ResidentDaemonSystemdUserControlError) as exc_info:
        run_systemd_user_command(plan, action="enable_now")

    assert exc_info.value.payload["failure_mode"] == "unit_missing"
