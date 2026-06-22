"""Tests for resident daemon service/control boundary contract."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_service_control_boundary


def test_daemon_service_control_boundary_exposes_allowed_control_and_deferred_service(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_service_control_boundary(
        runtime_root,
        host="localhost",
        port=39000,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_service_control_boundary"
    assert payload["control_plane"]["status"] == "cli_control_supported_local_mvp"
    assert payload["service_plane"]["status"] == "not_supported"
    assert "daemon-service-install" in payload["service_plane"]["deferred_commands"]
    allowed_commands = payload["control_plane"]["allowed_commands"]
    assert allowed_commands[0]["app_ui_exposure"] == "next_action_only"
    assert "daemon-start --host localhost --port 39000 --json" in allowed_commands[0]["command"]

