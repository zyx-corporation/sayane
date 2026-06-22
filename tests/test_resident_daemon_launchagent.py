"""Tests for macOS LaunchAgent preview/apply support."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import ResidentDaemonLaunchAgentApplyError, build_launchagent_plan, apply_launchagent_plan


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
