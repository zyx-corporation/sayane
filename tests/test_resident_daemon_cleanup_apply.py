"""Tests for resident daemon cleanup apply."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonCleanupApplyError,
    ResidentDaemonCleanupApplyTarget,
    apply_cleanup_decisions,
    build_cleanup_apply_preview,
    build_runtime_init_plan,
)
from sayane.app.daemon_runtime_init import apply_runtime_init


def test_cleanup_apply_removes_explicit_pid_and_lock_files(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    pid_path = runtime_root / "sayane-resident.pid"
    lock_path = runtime_root / "sayane-resident.lock"
    pid_path.write_text("12345\n", encoding="utf-8")
    lock_path.write_text("{}\n", encoding="utf-8")
    preview = build_cleanup_apply_preview(runtime_root)

    payload = apply_cleanup_decisions(
        runtime_root,
        targets=(
            ResidentDaemonCleanupApplyTarget.PID_FILE,
            ResidentDaemonCleanupApplyTarget.LOCK_FILE,
        ),
        confirm_operation_id=preview["operation_id"],
        confirm_preview_hash=preview["preview_hash"],
    )

    assert payload["kind"] == "resident_daemon_cleanup_apply_receipt"
    assert payload["result"] == "applied"
    assert payload["applied"] is True
    assert str(pid_path) in payload["removed_paths"]
    assert str(lock_path) in payload["removed_paths"]
    assert pid_path.exists() is False
    assert lock_path.exists() is False


def test_cleanup_apply_rejects_running_daemon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")
    monkeypatch.setattr("sayane.app.daemon_process_control._is_pid_running", lambda pid: True)

    with pytest.raises(ResidentDaemonCleanupApplyError) as excinfo:
        apply_cleanup_decisions(
            runtime_root,
            targets=(ResidentDaemonCleanupApplyTarget.PID_FILE,),
        )

    assert excinfo.value.payload["failure_mode"] == "daemon_running"


def test_cleanup_apply_can_include_event_record(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")
    preview = build_cleanup_apply_preview(runtime_root)

    payload = apply_cleanup_decisions(
        runtime_root,
        targets=(ResidentDaemonCleanupApplyTarget.PID_FILE,),
        confirm_operation_id=preview["operation_id"],
        confirm_preview_hash=preview["preview_hash"],
        include_event_record=True,
    )

    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["surface"] == "daemon-cleanup-apply"
    assert payload["event_record"]["result"] == "succeeded"


def test_cleanup_apply_requires_matching_preview_confirmation(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    (runtime_root / "sayane-resident.pid").write_text("12345\n", encoding="utf-8")

    with pytest.raises(ResidentDaemonCleanupApplyError) as excinfo:
        apply_cleanup_decisions(
            runtime_root,
            targets=(ResidentDaemonCleanupApplyTarget.PID_FILE,),
        )

    assert excinfo.value.payload["failure_mode"] == "confirm_operation_id_missing"

    preview = build_cleanup_apply_preview(runtime_root)
    with pytest.raises(ResidentDaemonCleanupApplyError) as excinfo:
        apply_cleanup_decisions(
            runtime_root,
            targets=(ResidentDaemonCleanupApplyTarget.PID_FILE,),
            confirm_operation_id=preview["operation_id"],
            confirm_preview_hash="wrong-hash",
        )

    assert excinfo.value.payload["failure_mode"] == "confirm_preview_hash_mismatch"
