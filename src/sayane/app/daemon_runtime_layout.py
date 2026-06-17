"""Resident daemon runtime directory layout contract.

This module does not create directories or files. It defines the planned runtime
layout for a future resident daemon and validates that layout paths stay under
its runtime root.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def validate_runtime_child_path(path: Path, *, runtime_root: Path) -> None:
    """Raise when a planned runtime path escapes the runtime root."""
    if not _is_relative_to(path, runtime_root):
        msg = "resident daemon runtime paths must stay under runtime_root"
        raise ValueError(msg)


@dataclass(frozen=True)
class ResidentDaemonRuntimeLayout:
    """Plan-only directory layout contract for a future resident daemon."""

    runtime_root: Path
    pid_dirname: str = "pid"
    lock_dirname: str = "lock"
    socket_dirname: str = "socket"
    log_dirname: str = "log"
    temp_dirname: str = "tmp"
    state_dirname: str = "state"
    creates_directories: bool = False
    writes_files: bool = False

    @property
    def pid_dir(self) -> Path:
        """Return planned PID directory."""
        return self.runtime_root / self.pid_dirname

    @property
    def lock_dir(self) -> Path:
        """Return planned lock directory."""
        return self.runtime_root / self.lock_dirname

    @property
    def socket_dir(self) -> Path:
        """Return planned socket directory."""
        return self.runtime_root / self.socket_dirname

    @property
    def log_dir(self) -> Path:
        """Return planned log directory."""
        return self.runtime_root / self.log_dirname

    @property
    def temp_dir(self) -> Path:
        """Return planned temp directory."""
        return self.runtime_root / self.temp_dirname

    @property
    def state_dir(self) -> Path:
        """Return planned runtime state directory."""
        return self.runtime_root / self.state_dirname

    def __post_init__(self) -> None:
        for path in (
            self.pid_dir,
            self.lock_dir,
            self.socket_dir,
            self.log_dir,
            self.temp_dir,
            self.state_dir,
        ):
            validate_runtime_child_path(path, runtime_root=self.runtime_root)

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive runtime layout diagnostics."""
        return {
            "runtime_root": str(self.runtime_root),
            "pid_dir": str(self.pid_dir),
            "lock_dir": str(self.lock_dir),
            "socket_dir": str(self.socket_dir),
            "log_dir": str(self.log_dir),
            "temp_dir": str(self.temp_dir),
            "state_dir": str(self.state_dir),
            "creates_directories": self.creates_directories,
            "writes_files": self.writes_files,
            "is_filesystem_mutation": False,
        }
