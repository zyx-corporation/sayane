"""Tests for cross-platform daemon service target status."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_service_targets_status


def test_daemon_service_targets_status_lists_macos_linux_windows(tmp_path: Path) -> None:
    payload = build_daemon_service_targets_status(tmp_path / "run").public_metadata()

    assert payload["kind"] == "resident_daemon_service_targets_status"
    targets = {entry["target"]: entry for entry in payload["targets"]}
    assert targets["macos_launchagent"]["platform"] == "macos"
    assert "sayane app daemon-launchagent-bootstrap --json" in targets["macos_launchagent"]["commands"]
    assert targets["linux_systemd_user"]["platform"] == "linux"
    assert targets["windows_service"]["platform"] == "windows"
