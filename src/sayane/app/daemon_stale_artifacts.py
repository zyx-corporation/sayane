"""Read-only resident daemon stale artifact diagnostics.

This module does not create, delete, repair, or mutate filesystem artifacts. It
observes planned resident daemon artifact paths and returns conservative
classification metadata for future operator review.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Iterable

from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout


class ResidentDaemonArtifactKind(StrEnum):
    """Known resident daemon runtime artifact kinds."""

    RUNTIME_ROOT = "runtime_root"
    PID_FILE = "pid_file"
    LOCK_FILE = "lock_file"
    SOCKET_FILE = "socket_file"
    PID_DIR = "pid_dir"
    LOCK_DIR = "lock_dir"
    SOCKET_DIR = "socket_dir"
    LOG_DIR = "log_dir"
    TEMP_DIR = "temp_dir"
    STATE_DIR = "state_dir"


class ResidentDaemonArtifactStatus(StrEnum):
    """Conservative artifact diagnostic status."""

    MISSING = "missing"
    PRESENT_REVIEW_REQUIRED = "present_review_required"
    TYPE_MISMATCH_REVIEW_REQUIRED = "type_mismatch_review_required"


@dataclass(frozen=True)
class ResidentDaemonArtifactDiagnostic:
    """Read-only diagnostic for one planned daemon runtime artifact."""

    kind: ResidentDaemonArtifactKind
    path: Path
    expected_type: str
    exists: bool
    is_file: bool
    is_dir: bool
    is_socket: bool
    status: ResidentDaemonArtifactStatus
    manual_review_required: bool
    safe_to_delete: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive diagnostic metadata."""
        return {
            "kind": self.kind.value,
            "path": str(self.path),
            "expected_type": self.expected_type,
            "exists": self.exists,
            "is_file": self.is_file,
            "is_dir": self.is_dir,
            "is_socket": self.is_socket,
            "status": self.status.value,
            "manual_review_required": self.manual_review_required,
            "safe_to_delete": self.safe_to_delete,
            "mutates_filesystem": self.mutates_filesystem,
        }


@dataclass(frozen=True)
class ResidentDaemonStaleArtifactReport:
    """Read-only report for planned daemon runtime artifacts."""

    identity: ResidentDaemonIdentity
    layout: ResidentDaemonRuntimeLayout
    diagnostics: tuple[ResidentDaemonArtifactDiagnostic, ...]
    stale_artifact_policy: str = "manual_review_required"
    repairs_artifacts: bool = False
    deletes_artifacts: bool = False
    creates_artifacts: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public report metadata."""
        return {
            "kind": "resident_daemon_stale_artifact_diagnostic_preview",
            "preview_only": True,
            "runtime_root": str(self.layout.runtime_root),
            "stale_artifact_policy": self.stale_artifact_policy,
            "repairs_artifacts": self.repairs_artifacts,
            "deletes_artifacts": self.deletes_artifacts,
            "creates_artifacts": self.creates_artifacts,
            "mutates_filesystem": self.mutates_filesystem,
            "manual_review_required": any(
                diagnostic.manual_review_required for diagnostic in self.diagnostics
            ),
            "diagnostics": [diagnostic.public_metadata() for diagnostic in self.diagnostics],
        }


def _path_type_flags(path: Path) -> tuple[bool, bool, bool, bool]:
    exists = path.exists()
    return exists, path.is_file(), path.is_dir(), path.is_socket()


def _status_for(expected_type: str, *, exists: bool, is_file: bool, is_dir: bool, is_socket: bool) -> ResidentDaemonArtifactStatus:
    if not exists:
        return ResidentDaemonArtifactStatus.MISSING
    if expected_type == "file" and not is_file:
        return ResidentDaemonArtifactStatus.TYPE_MISMATCH_REVIEW_REQUIRED
    if expected_type == "directory" and not is_dir:
        return ResidentDaemonArtifactStatus.TYPE_MISMATCH_REVIEW_REQUIRED
    if expected_type == "socket" and not is_socket:
        return ResidentDaemonArtifactStatus.TYPE_MISMATCH_REVIEW_REQUIRED
    return ResidentDaemonArtifactStatus.PRESENT_REVIEW_REQUIRED


def _diagnostic(kind: ResidentDaemonArtifactKind, path: Path, *, expected_type: str) -> ResidentDaemonArtifactDiagnostic:
    exists, is_file, is_dir, is_socket = _path_type_flags(path)
    status = _status_for(
        expected_type,
        exists=exists,
        is_file=is_file,
        is_dir=is_dir,
        is_socket=is_socket,
    )
    return ResidentDaemonArtifactDiagnostic(
        kind=kind,
        path=path,
        expected_type=expected_type,
        exists=exists,
        is_file=is_file,
        is_dir=is_dir,
        is_socket=is_socket,
        status=status,
        manual_review_required=status is not ResidentDaemonArtifactStatus.MISSING,
    )


def _planned_artifacts(
    identity: ResidentDaemonIdentity,
    layout: ResidentDaemonRuntimeLayout,
) -> Iterable[tuple[ResidentDaemonArtifactKind, Path, str]]:
    return (
        (ResidentDaemonArtifactKind.RUNTIME_ROOT, layout.runtime_root, "directory"),
        (ResidentDaemonArtifactKind.PID_FILE, identity.pid_path, "file"),
        (ResidentDaemonArtifactKind.LOCK_FILE, identity.lock_path, "file"),
        (ResidentDaemonArtifactKind.SOCKET_FILE, identity.socket_path, "socket"),
        (ResidentDaemonArtifactKind.PID_DIR, layout.pid_dir, "directory"),
        (ResidentDaemonArtifactKind.LOCK_DIR, layout.lock_dir, "directory"),
        (ResidentDaemonArtifactKind.SOCKET_DIR, layout.socket_dir, "directory"),
        (ResidentDaemonArtifactKind.LOG_DIR, layout.log_dir, "directory"),
        (ResidentDaemonArtifactKind.TEMP_DIR, layout.temp_dir, "directory"),
        (ResidentDaemonArtifactKind.STATE_DIR, layout.state_dir, "directory"),
    )


def build_stale_artifact_report(
    *,
    identity: ResidentDaemonIdentity,
    layout: ResidentDaemonRuntimeLayout,
) -> ResidentDaemonStaleArtifactReport:
    """Build a read-only stale artifact diagnostic report."""
    diagnostics = tuple(
        _diagnostic(kind, path, expected_type=expected_type)
        for kind, path, expected_type in _planned_artifacts(identity, layout)
    )
    return ResidentDaemonStaleArtifactReport(
        identity=identity,
        layout=layout,
        diagnostics=diagnostics,
    )
