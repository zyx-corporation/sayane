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
    assert payload["service_plane"]["status"] in {
        "mvp_contract_only_non_macos",
        "mvp_macos_launchagent_preview_apply_cli_only",
        "post_mvp_macos_launchagent_preview_apply_cli_only",
        "post_mvp_linux_systemd_user_preview_apply_cli_only",
    }
    assert "daemon-service-install" in payload["service_plane"]["deferred_commands"]
    assert "daemon-service-update" in payload["service_plane"]["deferred_commands"]
    assert "macos_launchagent" in payload["service_plane"]["platform_targets"]
    assert "windows_service" in payload["service_plane"]["platform_targets"]
    assert payload["service_plane"]["update_strategy"] == "not_supported_in_mvp"
    assert payload["control_plane"]["recovery_policy"]
    lifecycle_operations = payload["service_plane"]["lifecycle_operations"]
    assert lifecycle_operations[0]["operation"] == "install"
    assert lifecycle_operations[-1]["operation"] == "update"
    assert all(item["status"] == "not_supported_in_mvp" for item in lifecycle_operations)
    allowed_commands = payload["control_plane"]["allowed_commands"]
    assert allowed_commands[0]["app_ui_exposure"] == "next_action_only"
    assert "daemon-start --host localhost --port 39000 --json" in allowed_commands[0]["command"]
    assert payload["app_ui_policy"]["allowed_control_exposure"]
    if payload["service_plane"]["status"] in {
        "mvp_macos_launchagent_preview_apply_cli_only",
        "post_mvp_macos_launchagent_preview_apply_cli_only",
    }:
        assert any(
            item["command"] == "sayane app daemon-launchagent-bootstrap --json"
            for item in payload["service_plane"]["allowed_commands"]
        )
