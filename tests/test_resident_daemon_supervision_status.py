"""Tests for resident daemon supervision status."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_supervision_status


def test_daemon_supervision_status_exposes_passive_visibility_and_cli_recovery(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_supervision_status(
        runtime_root,
        host="localhost",
        port=39000,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_supervision_status"
    assert payload["supervision_mode"] == "passive_local_observation_with_cli_recovery"
    assert payload["passive_visibility"]["status"] == "supported"
    assert payload["active_supervision"]["status"] == "limited_cli_only"
    assert payload["background_surfaces"]["status"] == "not_supported"
    candidates = payload["background_surfaces"]["candidate_surfaces"]
    assert candidates[0]["surface"] == "tray_supervision"
    assert candidates[1]["surface"] == "menu_bar_supervision"
    assert candidates[2]["surface"] == "login_item_or_background_agent_visibility"
    assert all(item["status"] == "separate_plan_required" for item in candidates)
    assert "sayane app daemon-service-control-boundary --json" in payload["recovery_entrypoints"]
