"""Resident daemon process identity contract.

This module does not write PID files or acquire locks. It describes the future
resident daemon process identity paths and validates that they stay inside the
resident runtime directory.
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


def validate_runtime_local_path(path: Path, *, runtime_dir: Path) -> None:
    """Raise when a path escapes the resident runtime directory."""
    if not _is_relative_to(path, runtime_dir):
        msg = "resident daemon identity paths must stay under runtime_dir"
        raise ValueError(msg)


@dataclass(frozen=True)
class ResidentDaemonIdentity:
    """Plan-only identity contract for a future resident daemon process."""

    runtime_dir: Path
    name: str = "sayane-resident"
    pid_filename: str = "sayane-resident.pid"
    lock_filename: str = "sayane-resident.lock"
    socket_filename: str = "sayane-resident.sock"
    writes_files: bool = False
    acquires_lock: bool = False
    stale_lock_policy: str = "manual_review_required"

    @property
    def pid_path(self) -> Path:
        """Return the planned PID file path."""
        return self.runtime_dir / self.pid_filename

    @property
    def lock_path(self) -> Path:
        """Return the planned lock file path."""
        return self.runtime_dir / self.lock_filename

    @property
    def socket_path(self) -> Path:
        """Return the planned local socket path."""
        return self.runtime_dir / self.socket_filename

    def __post_init__(self) -> None:
        for path in (self.pid_path, self.lock_path, self.socket_path):
            validate_runtime_local_path(path, runtime_dir=self.runtime_dir)

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive daemon identity diagnostics."""
        return {
            "name": self.name,
            "runtime_dir": str(self.runtime_dir),
            "pid_path": str(self.pid_path),
            "lock_path": str(self.lock_path),
            "socket_path": str(self.socket_path),
            "writes_files": self.writes_files,
            "acquires_lock": self.acquires_lock,
            "stale_lock_policy": self.stale_lock_policy,
            "is_process_control": False,
        }
