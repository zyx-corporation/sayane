"""Tests for resident daemon repair apply."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonRepairApplyError,
    ResidentDaemonRepairApplyTarget,
    apply_runtime_repairs,
    build_repair_apply_preview,
    build_runtime_init_plan,
)
from sayane.app.daemon_runtime_init import apply_runtime_init


def test_repair_apply_creates_explicit_runtime_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    preview = build_repair_apply_preview(runtime_root)

    payload = apply_runtime_repairs(
        runtime_root,
        targets=(
            ResidentDaemonRepairApplyTarget.RUNTIME_ROOT,
            ResidentDaemonRepairApplyTarget.PID_DIR,
            ResidentDaemonRepairApplyTarget.LOG_DIR,
        ),
        confirm_operation_id=preview["operation_id"],
        confirm_preview_hash=preview["preview_hash"],
    )

    assert payload["kind"] == "resident_daemon_repair_apply_receipt"
    assert payload["result"] == "applied"
    assert payload["applied"] is True
    assert str(runtime_root) in payload["created_paths"]
    assert str(runtime_root / "log") in payload["created_paths"]
    assert runtime_root.exists() is True
    assert (runtime_root / "pid").exists() is True
    assert (runtime_root / "log").exists() is True


def test_repair_apply_rejects_running_daemon(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")
    monkeypatch.setattr("sayane.app.daemon_process_control._is_pid_running", lambda pid: True)

    with pytest.raises(ResidentDaemonRepairApplyError) as excinfo:
        apply_runtime_repairs(
            runtime_root,
            targets=(ResidentDaemonRepairApplyTarget.LOG_DIR,),
        )

    assert excinfo.value.payload["failure_mode"] == "daemon_running"


def test_repair_apply_can_include_event_record(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    preview = build_repair_apply_preview(runtime_root)

    payload = apply_runtime_repairs(
        runtime_root,
        targets=(ResidentDaemonRepairApplyTarget.RUNTIME_ROOT,),
        confirm_operation_id=preview["operation_id"],
        confirm_preview_hash=preview["preview_hash"],
        include_event_record=True,
    )

    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["surface"] == "daemon-repair-apply"
    assert payload["event_record"]["result"] == "succeeded"


def test_repair_apply_requires_matching_preview_confirmation(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"

    with pytest.raises(ResidentDaemonRepairApplyError) as excinfo:
        apply_runtime_repairs(
            runtime_root,
            targets=(ResidentDaemonRepairApplyTarget.RUNTIME_ROOT,),
        )

    assert excinfo.value.payload["failure_mode"] == "confirm_operation_id_missing"

    preview = build_repair_apply_preview(runtime_root)
    with pytest.raises(ResidentDaemonRepairApplyError) as excinfo:
        apply_runtime_repairs(
            runtime_root,
            targets=(ResidentDaemonRepairApplyTarget.RUNTIME_ROOT,),
            confirm_operation_id=preview["operation_id"],
            confirm_preview_hash="wrong-hash",
        )

    assert excinfo.value.payload["failure_mode"] == "confirm_preview_hash_mismatch"


def test_repair_apply_requires_manual_review_for_conflicting_path(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir(parents=True)
    (runtime_root / "log").write_text("not-a-dir\n", encoding="utf-8")
    preview = build_repair_apply_preview(runtime_root)

    with pytest.raises(ResidentDaemonRepairApplyError) as excinfo:
        apply_runtime_repairs(
            runtime_root,
            targets=(ResidentDaemonRepairApplyTarget.LOG_DIR,),
            confirm_operation_id=preview["operation_id"],
            confirm_preview_hash=preview["preview_hash"],
        )

    assert excinfo.value.payload["result"] == "requires_review"
    assert excinfo.value.payload["failure_mode"] == "log_dir_review_required"
