"""Tests for resident daemon overview preview."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_overview_preview, create_local_capability_token


def test_daemon_overview_preview_aggregates_status_and_next_actions(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_overview_preview(
        runtime_root,
        capability=create_local_capability_token(["ui"]),
    )

    assert payload["kind"] == "resident_daemon_overview_preview"
    assert payload["is_daemon_surface"] is True
    assert payload["is_preview"] is True
    assert payload["status"]["kind"] == "resident_daemon_lifecycle_status"
    assert payload["liveness"]["kind"] == "resident_daemon_liveness_diagnostic_preview"
    assert payload["readiness"]["kind"] == "resident_daemon_readiness_diagnostic_preview"
    assert payload["runtime_init"]["kind"] == "resident_daemon_runtime_init_plan"
    assert payload["cleanup_preview"]["kind"] == "resident_daemon_cleanup_apply_preview"
    assert payload["repair_preview"]["kind"] == "resident_daemon_repair_apply_preview"
    assert payload["packaging_status"]["kind"] == "resident_daemon_packaging_status"
    assert payload["service_control_boundary"]["kind"] == "resident_daemon_service_control_boundary"
    assert payload["supervision_status"]["kind"] == "resident_daemon_supervision_status"
    assert payload["recovery_consent_status"]["kind"] == "resident_daemon_recovery_consent_status"
    assert payload["next_actions"][0]["command"] == "sayane app daemon-runtime-init --json"


def test_daemon_overview_preview_suggests_readiness_when_running(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir(parents=True)
    for child in ("pid", "lock", "socket", "log", "tmp", "state"):
        (runtime_root / child).mkdir()
    (runtime_root / "sayane-resident.pid").write_text("12345\n", encoding="utf-8")
    (runtime_root / "sayane-resident.lock").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr("sayane.app.daemon_process_control._is_pid_running", lambda pid: True)
    monkeypatch.setattr("sayane.app.daemon_process_control._healthcheck", lambda url, timeout=0.2: True)

    payload = build_daemon_overview_preview(
        runtime_root,
        capability=create_local_capability_token(["ui"]),
    )

    commands = [action["command"] for action in payload["next_actions"]]
    assert "sayane app daemon-readiness-diagnostic --json" in commands


def test_daemon_overview_preview_suggests_daemon_start_when_initialized_but_stopped(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir(parents=True)
    for child in ("pid", "lock", "socket", "log", "tmp", "state"):
        (runtime_root / child).mkdir()

    payload = build_daemon_overview_preview(
        runtime_root,
        capability=create_local_capability_token(["ui"]),
    )

    commands = [action["command"] for action in payload["next_actions"]]
    assert "sayane app daemon-start --json" in commands
