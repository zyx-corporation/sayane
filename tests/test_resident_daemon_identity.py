"""Tests for resident daemon process identity contract (#191)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app.daemon_identity import (
    ResidentDaemonIdentity,
    validate_runtime_local_path,
)


def test_daemon_identity_defaults_are_plan_only(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)

    assert identity.pid_path == runtime_dir / "sayane-resident.pid"
    assert identity.lock_path == runtime_dir / "sayane-resident.lock"
    assert identity.socket_path == runtime_dir / "sayane-resident.sock"
    assert identity.writes_files is False
    assert identity.acquires_lock is False
    assert identity.public_metadata() == {
        "name": "sayane-resident",
        "runtime_dir": str(runtime_dir),
        "pid_path": str(runtime_dir / "sayane-resident.pid"),
        "lock_path": str(runtime_dir / "sayane-resident.lock"),
        "socket_path": str(runtime_dir / "sayane-resident.sock"),
        "writes_files": False,
        "acquires_lock": False,
        "stale_lock_policy": "manual_review_required",
        "is_process_control": False,
    }


def test_daemon_identity_does_not_write_files(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)

    assert runtime_dir.exists() is False
    assert identity.pid_path.exists() is False
    assert identity.lock_path.exists() is False
    assert identity.socket_path.exists() is False


def test_validate_runtime_local_path_accepts_runtime_child(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"

    validate_runtime_local_path(runtime_dir / "sayane-resident.pid", runtime_dir=runtime_dir)


def test_validate_runtime_local_path_rejects_escape(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"
    outside = tmp_path / "outside.pid"

    with pytest.raises(ValueError, match="runtime_dir"):
        validate_runtime_local_path(outside, runtime_dir=runtime_dir)


def test_daemon_identity_rejects_custom_filename_escape(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime"

    with pytest.raises(ValueError, match="runtime_dir"):
        ResidentDaemonIdentity(runtime_dir=runtime_dir, pid_filename="../escape.pid")
