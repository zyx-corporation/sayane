"""Tests for resident daemon runtime directory layout contract (#194)."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app.daemon_runtime_layout import (
    ResidentDaemonRuntimeLayout,
    validate_runtime_child_path,
)


def test_runtime_layout_defaults_are_plan_only(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)

    assert layout.pid_dir == runtime_root / "pid"
    assert layout.lock_dir == runtime_root / "lock"
    assert layout.socket_dir == runtime_root / "socket"
    assert layout.log_dir == runtime_root / "log"
    assert layout.temp_dir == runtime_root / "tmp"
    assert layout.state_dir == runtime_root / "state"
    assert layout.creates_directories is False
    assert layout.writes_files is False
    assert layout.public_metadata() == {
        "runtime_root": str(runtime_root),
        "pid_dir": str(runtime_root / "pid"),
        "lock_dir": str(runtime_root / "lock"),
        "socket_dir": str(runtime_root / "socket"),
        "log_dir": str(runtime_root / "log"),
        "temp_dir": str(runtime_root / "tmp"),
        "state_dir": str(runtime_root / "state"),
        "creates_directories": False,
        "writes_files": False,
        "is_filesystem_mutation": False,
    }


def test_runtime_layout_does_not_touch_filesystem(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)

    assert runtime_root.exists() is False
    assert layout.pid_dir.exists() is False
    assert layout.lock_dir.exists() is False
    assert layout.socket_dir.exists() is False
    assert layout.log_dir.exists() is False
    assert layout.temp_dir.exists() is False
    assert layout.state_dir.exists() is False


def test_validate_runtime_child_path_accepts_runtime_child(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"

    validate_runtime_child_path(runtime_root / "pid", runtime_root=runtime_root)


def test_validate_runtime_child_path_rejects_outside_path(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    outside = tmp_path / "outside"

    with pytest.raises(ValueError, match="runtime_root"):
        validate_runtime_child_path(outside, runtime_root=runtime_root)


def test_runtime_layout_rejects_parent_relative_dirname(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"

    with pytest.raises(ValueError, match="runtime_root"):
        ResidentDaemonRuntimeLayout(runtime_root=runtime_root, pid_dirname="../outside")
