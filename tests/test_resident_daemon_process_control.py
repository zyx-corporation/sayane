"""Tests for minimal resident daemon process control."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonProcessControlError,
    build_daemon_status_report,
    build_runtime_init_plan,
    start_resident_daemon,
    stop_resident_daemon,
)
from sayane.app.daemon_runtime_init import apply_runtime_init
from sayane.app import daemon_process_control as control


class _FakeProcess:
    def __init__(self, pid: int) -> None:
        self.pid = pid


def test_daemon_status_is_stopped_before_start(tmp_path: Path) -> None:
    payload = build_daemon_status_report(tmp_path / "run").public_metadata()

    assert payload["kind"] == "resident_daemon_lifecycle_status"
    assert payload["state"] == "stopped"
    assert payload["is_running_daemon"] is False
    assert payload["runtime_initialized"] is False
    assert payload["pid_file_status"] == "missing"


def test_daemon_start_requires_runtime_init(tmp_path: Path) -> None:
    with pytest.raises(ResidentDaemonProcessControlError) as excinfo:
        start_resident_daemon(tmp_path / "run")

    assert excinfo.value.payload["result"] == "aborted"
    assert excinfo.value.payload["failure_mode"] == "runtime_init_required"


def test_daemon_start_writes_pid_and_lock_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    monkeypatch.setattr(control, "_spawn_daemon_subprocess", lambda command, log_path: _FakeProcess(43210))
    monkeypatch.setattr(control, "_wait_for_bridge_health", lambda url, wait_seconds: True)

    payload = start_resident_daemon(runtime_root, host="localhost", port=39000)

    assert payload["operation"] == "start"
    assert payload["result"] == "started"
    assert payload["applied"] is True
    assert payload["pid"] == 43210
    assert runtime_root.joinpath("sayane-resident.pid").read_text(encoding="utf-8").strip() == "43210"
    assert runtime_root.joinpath("sayane-resident.lock").is_file()


def test_daemon_start_can_include_event_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    monkeypatch.setattr(
        control,
        "_spawn_daemon_subprocess",
        lambda command, log_path: _FakeProcess(43210),
    )
    monkeypatch.setattr(control, "_wait_for_bridge_health", lambda url, wait_seconds: True)

    payload = start_resident_daemon(runtime_root, include_event_record=True)

    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["category"] == "process"
    assert payload["event_record"]["surface"] == "daemon-start"
    assert payload["event_record"]["result"] == "succeeded"


def test_daemon_start_requires_manual_review_for_stale_pid(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    runtime_root.joinpath("sayane-resident.pid").write_text("12345\n", encoding="utf-8")

    with pytest.raises(ResidentDaemonProcessControlError) as excinfo:
        start_resident_daemon(runtime_root)

    assert excinfo.value.payload["result"] == "requires_review"
    assert excinfo.value.payload["failure_mode"] == "stale_pid_file"


def test_daemon_stop_removes_pid_and_lock_files(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    runtime_root.joinpath("sayane-resident.pid").write_text("555\n", encoding="utf-8")
    runtime_root.joinpath("sayane-resident.lock").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(control, "_is_pid_running", lambda pid: True if pid == 555 else False)
    monkeypatch.setattr(control, "_signal_process", lambda pid, sig: None)
    monkeypatch.setattr(control, "_wait_for_process_exit", lambda pid, wait_seconds: True)

    payload = stop_resident_daemon(runtime_root)

    assert payload["result"] == "stopped"
    assert payload["applied"] is True
    assert runtime_root.joinpath("sayane-resident.pid").exists() is False
    assert runtime_root.joinpath("sayane-resident.lock").exists() is False


def test_daemon_stop_returns_no_action_when_not_running(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))

    payload = stop_resident_daemon(runtime_root)

    assert payload["result"] == "no_action"
    assert payload["applied"] is False
