"""Read-only resident daemon PID file parse diagnostics.

This module reads at most the planned PID file content and classifies it. It
does not create, delete, repair, or mutate filesystem artifacts and does not
probe or control processes.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from sayane.app.daemon_identity import ResidentDaemonIdentity


class ResidentDaemonPidParseStatus(StrEnum):
    """Conservative PID file parse status."""

    MISSING = "missing"
    UNREADABLE = "unreadable"
    EMPTY = "empty"
    INVALID = "invalid"
    PARSED = "parsed"


@dataclass(frozen=True)
class ResidentDaemonPidFileDiagnostic:
    """Read-only diagnostic for the planned resident daemon PID file."""

    path: Path
    exists: bool
    status: ResidentDaemonPidParseStatus
    parsed_pid: int | None = None
    raw_value_preview: str | None = None
    error: str | None = None
    manual_review_required: bool = False
    proves_liveness: bool = False
    probes_process: bool = False
    controls_process: bool = False
    mutates_filesystem: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return public PID file diagnostic metadata."""
        return {
            "kind": "resident_daemon_pid_file_parse_diagnostic_preview",
            "preview_only": True,
            "path": str(self.path),
            "exists": self.exists,
            "status": self.status.value,
            "parsed_pid": self.parsed_pid,
            "raw_value_preview": self.raw_value_preview,
            "error": self.error,
            "manual_review_required": self.manual_review_required,
            "proves_liveness": self.proves_liveness,
            "probes_process": self.probes_process,
            "controls_process": self.controls_process,
            "mutates_filesystem": self.mutates_filesystem,
        }


def _preview_raw_value(value: str, *, max_length: int = 64) -> str:
    sanitized = value.replace("\n", "\\n").replace("\r", "\\r")
    if len(sanitized) <= max_length:
        return sanitized
    return f"{sanitized[:max_length]}..."


def _parse_pid(value: str) -> int | None:
    stripped = value.strip()
    if not stripped:
        return None
    if not stripped.isdecimal():
        return None
    parsed = int(stripped, 10)
    if parsed <= 0:
        return None
    return parsed


def build_pid_file_diagnostic(
    identity: ResidentDaemonIdentity,
) -> ResidentDaemonPidFileDiagnostic:
    """Build a read-only PID file parse diagnostic."""
    path = identity.pid_path
    if not path.exists():
        return ResidentDaemonPidFileDiagnostic(
            path=path,
            exists=False,
            status=ResidentDaemonPidParseStatus.MISSING,
        )
    try:
        value = path.read_text(encoding="utf-8")
    except OSError as exc:
        return ResidentDaemonPidFileDiagnostic(
            path=path,
            exists=True,
            status=ResidentDaemonPidParseStatus.UNREADABLE,
            error=f"{exc.__class__.__name__}: {exc}",
            manual_review_required=True,
        )
    if not value.strip():
        return ResidentDaemonPidFileDiagnostic(
            path=path,
            exists=True,
            status=ResidentDaemonPidParseStatus.EMPTY,
            raw_value_preview=_preview_raw_value(value),
            manual_review_required=True,
        )
    parsed_pid = _parse_pid(value)
    if parsed_pid is None:
        return ResidentDaemonPidFileDiagnostic(
            path=path,
            exists=True,
            status=ResidentDaemonPidParseStatus.INVALID,
            raw_value_preview=_preview_raw_value(value),
            manual_review_required=True,
        )
    return ResidentDaemonPidFileDiagnostic(
        path=path,
        exists=True,
        status=ResidentDaemonPidParseStatus.PARSED,
        parsed_pid=parsed_pid,
        raw_value_preview=_preview_raw_value(value),
        manual_review_required=True,
    )
