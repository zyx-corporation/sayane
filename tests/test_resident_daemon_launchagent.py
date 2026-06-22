"""Tests for macOS LaunchAgent preview/apply support."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonLaunchAgentApplyError,
    ResidentDaemonLaunchAgentControlError,
    apply_launchagent_plan,
    build_launchagent_plan,
    run_launchagent_command,
)


def test_launchagent_plan_exposes_plist_and_launchctl_commands(tmp_path: Path) -> None:
    plan = build_launchagent_plan(tmp_path / "run", host="localhost", port=39000, sayane_home=tmp_path / "home")
    payload = plan.public_metadata()

    assert payload["kind"] == "resident_daemon_launchagent_plan"
    assert payload["service_manager"] == "launchd"
    assert payload["platform"] == "macos"
    assert "launchctl bootstrap" in payload["launchctl_commands"]["bootstrap"]
    assert payload["label"] == "com.sayane.resident.bridge"


def test_launchagent_apply_writes_plist_after_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan = build_launchagent_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    receipt = apply_launchagent_plan(
        plan,
        confirm_operation_id=plan.operation_id,
        confirm_preview_hash=plan.preview_hash(),
    )

    assert receipt["kind"] == "resident_daemon_launchagent_receipt"
    assert Path(receipt["plist_path"]).is_file()


def test_launchagent_apply_rejects_mismatched_confirmation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    plan = build_launchagent_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    with pytest.raises(ResidentDaemonLaunchAgentApplyError):
        apply_launchagent_plan(plan, confirm_operation_id="bad", confirm_preview_hash="bad")


def test_launchagent_control_runs_bootstrap_on_macos(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_launchagent.sys.platform", "darwin")
    plan = build_launchagent_plan(tmp_path / "run", sayane_home=tmp_path / "home")
    plan.plist_path.parent.mkdir(parents=True, exist_ok=True)
    plan.plist_path.write_text(plan.plist_xml(), encoding="utf-8")

    def _fake_run(command, *, capture_output, text, check):
        assert command[:2] == ["launchctl", "bootstrap"]
        assert capture_output is True
        assert text is True
        assert check is False
        return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")

    monkeypatch.setattr("sayane.app.daemon_launchagent.subprocess.run", _fake_run)

    payload = run_launchagent_command(plan, action="bootstrap")

    assert payload["kind"] == "resident_daemon_launchagent_control_receipt"
    assert payload["action"] == "bootstrap"
    assert payload["result"] == "completed"
    assert payload["applied"] is True


def test_launchagent_control_rejects_missing_plist(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_launchagent.sys.platform", "darwin")
    plan = build_launchagent_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    with pytest.raises(ResidentDaemonLaunchAgentControlError) as exc_info:
        run_launchagent_command(plan, action="bootstrap")

    assert exc_info.value.payload["failure_mode"] == "plist_missing"


def test_launchagent_control_rejects_non_macos(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr("sayane.app.daemon_launchagent.sys.platform", "linux")
    plan = build_launchagent_plan(tmp_path / "run", sayane_home=tmp_path / "home")

    with pytest.raises(ResidentDaemonLaunchAgentControlError) as exc_info:
        run_launchagent_command(plan, action="kickstart")

    assert exc_info.value.payload["failure_mode"] == "platform_not_supported"
