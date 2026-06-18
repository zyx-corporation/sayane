"""Tests for resident daemon runtime initialization."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonRuntimeInitStatus,
    apply_runtime_init,
    build_runtime_init_plan,
)


def test_runtime_init_plan_is_preview_only_when_root_missing(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    plan = build_runtime_init_plan(runtime_root)

    assert plan.review_required is False
    assert plan.operation_id.startswith("runtime-init-")
    assert all(item.status is ResidentDaemonRuntimeInitStatus.CREATE for item in plan.items)
    assert runtime_root.exists() is False


def test_runtime_init_apply_creates_runtime_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    payload = apply_runtime_init(build_runtime_init_plan(runtime_root, operation_id="op-123"))

    assert payload["kind"] == "resident_daemon_runtime_init_apply"
    assert payload["operation_id"] == "op-123"
    assert payload["applied"] is True
    assert payload["mutates_filesystem"] is True
    assert payload["result"] == "applied"
    assert len(payload["created_paths"]) == 7
    assert (runtime_root / "pid").is_dir()
    assert (runtime_root / "lock").is_dir()
    assert (runtime_root / "socket").is_dir()
    assert (runtime_root / "log").is_dir()
    assert (runtime_root / "tmp").is_dir()
    assert (runtime_root / "state").is_dir()


def test_runtime_init_plan_requires_manual_review_for_conflicting_file(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "pid").write_text("conflict", encoding="utf-8")

    plan = build_runtime_init_plan(runtime_root)

    assert plan.review_required is True
    pid_item = next(item for item in plan.items if item.path_role == "pid_dir")
    assert pid_item.status is ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED
    assert str(runtime_root / "pid") in plan.public_metadata()["proposed_state"]["manual_review_paths"]
