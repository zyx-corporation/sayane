"""Minimal local-only resident daemon process control."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import urlopen
from uuid import uuid4

from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_lifecycle import ResidentDaemonState, validate_local_bind_host
from sayane.app.daemon_pid_diagnostics import (
    ResidentDaemonPidParseStatus,
    build_pid_file_diagnostic,
)
from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout


class ResidentDaemonProcessControlError(RuntimeError):
    """Structured resident daemon process-control failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


@dataclass(frozen=True)
class ResidentDaemonProcessStatusReport:
    """Actual local-only resident daemon status report."""

    runtime_root: Path
    host: str
    port: int
    state: ResidentDaemonState
    pid_path: Path
    lock_path: Path
    log_path: Path
    health_url: str
    pid: int | None = None
    pid_file_status: str = ResidentDaemonPidParseStatus.MISSING.value
    runtime_initialized: bool = False
    lock_exists: bool = False
    healthcheck_ok: bool = False
    manual_review_required: bool = False
    failure_mode: str | None = None
    notes: tuple[str, ...] = ()

    @property
    def is_running_daemon(self) -> bool:
        return self.state in (
            ResidentDaemonState.STARTING,
            ResidentDaemonState.RUNNING,
        )

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_lifecycle_status",
            "state": self.state.value,
            "mode": "bridge_delegation",
            "host": self.host,
            "port": self.port,
            "runtime_backend": "bridge_subprocess_local",
            "unlock_session_binding": "unbound",
            "capability_policy": "local_development",
            "is_local_bind": True,
            "notes": list(self.notes),
            "is_running_daemon": self.is_running_daemon,
            "runtime_root": str(self.runtime_root),
            "pid_path": str(self.pid_path),
            "lock_path": str(self.lock_path),
            "log_path": str(self.log_path),
            "health_url": self.health_url,
            "pid": self.pid,
            "pid_file_status": self.pid_file_status,
            "runtime_initialized": self.runtime_initialized,
            "lock_exists": self.lock_exists,
            "healthcheck_ok": self.healthcheck_ok,
            "manual_review_required": self.manual_review_required,
            "failure_mode": self.failure_mode,
        }


@dataclass(frozen=True)
class ResidentDaemonProcessControlReceipt:
    """Structured start/stop/restart receipt."""

    operation: str
    operation_id: str
    runtime_root: Path
    host: str
    port: int
    state_before: str
    state_after: str
    result: str
    applied: bool
    pid_path: Path
    lock_path: Path
    log_path: Path
    health_url: str
    pid: int | None = None
    failure_mode: str | None = None
    recovery_note: str | None = None
    command: tuple[str, ...] = ()
    manual_review_required: bool = False
    created_at: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_process_control_receipt",
            "operation": self.operation,
            "operation_id": self.operation_id,
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "result": self.result,
            "applied": self.applied,
            "pid_path": str(self.pid_path),
            "lock_path": str(self.lock_path),
            "log_path": str(self.log_path),
            "health_url": self.health_url,
            "pid": self.pid,
            "failure_mode": self.failure_mode,
            "recovery_note": self.recovery_note,
            "command": list(self.command),
            "manual_review_required": self.manual_review_required,
            "controls_process": self.operation in {"start", "stop", "restart"},
            "writes_pid_file": self.operation in {"start", "restart"},
            "acquires_lock": self.operation in {"start", "restart"},
            "exposes_ipc": self.operation in {"start", "restart"},
            "local_only": True,
            "created_at": self.created_at or datetime.now(UTC).isoformat(),
        }


def _runtime_initialized(layout: ResidentDaemonRuntimeLayout) -> bool:
    return layout.runtime_root.is_dir() and all(
        path.is_dir()
        for path in (
            layout.pid_dir,
            layout.lock_dir,
            layout.socket_dir,
            layout.log_dir,
            layout.temp_dir,
            layout.state_dir,
        )
    )


def _is_pid_running(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _healthcheck(url: str, *, timeout: float = 0.2) -> bool:
    try:
        with urlopen(url, timeout=timeout) as response:  # noqa: S310
            return response.status == 200
    except URLError:
        return False
    except OSError:
        return False


def _wait_for_bridge_health(url: str, *, wait_seconds: float) -> bool:
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if _healthcheck(url):
            return True
        time.sleep(0.1)
    return _healthcheck(url)


def _spawn_daemon_subprocess(command: list[str], log_path: Path) -> subprocess.Popen[str]:
    log_handle = log_path.open("a", encoding="utf-8")
    return subprocess.Popen(  # noqa: S603
        command,
        stdout=log_handle,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        start_new_session=True,
    )


def _write_lock_file(path: Path, payload: dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def _remove_file_if_exists(path: Path) -> None:
    try:
        path.unlink()
    except FileNotFoundError:
        return


def _wait_for_process_exit(pid: int, *, wait_seconds: float) -> bool:
    deadline = time.monotonic() + wait_seconds
    while time.monotonic() < deadline:
        if not _is_pid_running(pid):
            return True
        time.sleep(0.1)
    return not _is_pid_running(pid)


def _signal_process(pid: int, sig: int) -> None:
    os.kill(pid, sig)


def build_daemon_status_report(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonProcessStatusReport:
    """Build an actual local-only daemon status report."""
    validate_local_bind_host(host)
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    pid_diagnostic = build_pid_file_diagnostic(identity)
    runtime_initialized = _runtime_initialized(layout)
    lock_exists = identity.lock_path.exists()
    health_url = f"http://{host}:{port}/health"

    notes: list[str] = []
    state = ResidentDaemonState.STOPPED
    pid: int | None = None
    healthcheck_ok = False
    manual_review_required = False
    failure_mode: str | None = None

    if pid_diagnostic.status is ResidentDaemonPidParseStatus.MISSING:
        if lock_exists:
            state = ResidentDaemonState.FAILED
            manual_review_required = True
            failure_mode = "lock_without_pid"
            notes.append("lock file exists without pid file")
    elif pid_diagnostic.status in (
        ResidentDaemonPidParseStatus.UNREADABLE,
        ResidentDaemonPidParseStatus.EMPTY,
        ResidentDaemonPidParseStatus.INVALID,
    ):
        state = ResidentDaemonState.FAILED
        manual_review_required = True
        failure_mode = f"pid_{pid_diagnostic.status.value}"
        notes.append("pid file requires manual review")
    else:
        pid = pid_diagnostic.parsed_pid
        if pid is not None and _is_pid_running(pid):
            healthcheck_ok = _healthcheck(health_url)
            state = ResidentDaemonState.RUNNING if healthcheck_ok else ResidentDaemonState.STARTING
            if not lock_exists:
                notes.append("process is running without lock file")
        else:
            state = ResidentDaemonState.FAILED
            manual_review_required = True
            failure_mode = "stale_pid_file"
            notes.append("pid file references a non-running process")

    return ResidentDaemonProcessStatusReport(
        runtime_root=runtime_root,
        host=host,
        port=port,
        state=state,
        pid_path=identity.pid_path,
        lock_path=identity.lock_path,
        log_path=layout.log_dir / "sayane-resident.log",
        health_url=health_url,
        pid=pid,
        pid_file_status=pid_diagnostic.status.value,
        runtime_initialized=runtime_initialized,
        lock_exists=lock_exists,
        healthcheck_ok=healthcheck_ok,
        manual_review_required=manual_review_required,
        failure_mode=failure_mode,
        notes=tuple(notes),
    )


def _build_control_receipt(
    *,
    operation: str,
    runtime_root: Path,
    host: str,
    port: int,
    state_before: ResidentDaemonState,
    state_after: ResidentDaemonState,
    result: str,
    applied: bool,
    pid_path: Path,
    lock_path: Path,
    log_path: Path,
    health_url: str,
    pid: int | None = None,
    failure_mode: str | None = None,
    recovery_note: str | None = None,
    command: tuple[str, ...] = (),
    manual_review_required: bool = False,
    operation_id: str | None = None,
    include_event_record: bool = False,
) -> dict[str, Any]:
    payload = ResidentDaemonProcessControlReceipt(
        operation=operation,
        operation_id=operation_id or f"daemon-{operation}-{uuid4().hex[:12]}",
        runtime_root=runtime_root,
        host=host,
        port=port,
        state_before=state_before.value,
        state_after=state_after.value,
        result=result,
        applied=applied,
        pid_path=pid_path,
        lock_path=lock_path,
        log_path=log_path,
        health_url=health_url,
        pid=pid,
        failure_mode=failure_mode,
        recovery_note=recovery_note,
        command=command,
        manual_review_required=manual_review_required,
    ).public_metadata()
    if include_event_record:
        from sayane.app.daemon_event_records import build_process_control_event_record

        payload["event_record"] = build_process_control_event_record(
            operation_id=payload["operation_id"],
            operation=operation,
            runtime_root=runtime_root,
            result=result,
            state_before=state_before.value,
            state_after=state_after.value,
            host=host,
            port=port,
            pid=pid,
            failure_mode=failure_mode,
            manual_review_required=manual_review_required,
            applied=applied,
        ).public_metadata()
    return payload


def start_resident_daemon(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    wait_seconds: float = 5.0,
    include_event_record: bool = False,
) -> dict[str, Any]:
    """Start a minimal local-only resident daemon subprocess."""
    status = build_daemon_status_report(runtime_root, host=host, port=port)
    if not status.runtime_initialized:
        raise ResidentDaemonProcessControlError(
            "runtime init must complete before daemon-start",
            payload=_build_control_receipt(
                operation="start",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=status.state,
                result="aborted",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                failure_mode="runtime_init_required",
                recovery_note="Run daemon-runtime-init --apply before daemon-start.",
                include_event_record=include_event_record,
            ),
        )
    if status.is_running_daemon:
        raise ResidentDaemonProcessControlError(
            "resident daemon is already running",
            payload=_build_control_receipt(
                operation="start",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=status.state,
                result="aborted",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                pid=status.pid,
                failure_mode="already_running",
                recovery_note="Use daemon-status or daemon-restart for an existing process.",
                include_event_record=include_event_record,
            ),
        )
    if status.manual_review_required:
        raise ResidentDaemonProcessControlError(
            "resident daemon start requires manual review",
            payload=_build_control_receipt(
                operation="start",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=status.state,
                result="requires_review",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                pid=status.pid,
                failure_mode=status.failure_mode,
                recovery_note="Clear stale runtime artifacts only after manual review.",
                manual_review_required=True,
                include_event_record=include_event_record,
            ),
        )

    command = [
        sys.executable,
        "-m",
        "sayane.cli.main",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
    ]
    operation_id = f"daemon-start-{uuid4().hex[:12]}"
    lock_payload = {
        "kind": "resident_daemon_lock",
        "operation_id": operation_id,
        "host": host,
        "port": port,
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        _write_lock_file(status.lock_path, lock_payload)
    except FileExistsError as exc:
        raise ResidentDaemonProcessControlError(
            "lock file already exists",
            payload=_build_control_receipt(
                operation="start",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=ResidentDaemonState.FAILED,
                result="requires_review",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                failure_mode="lock_exists",
                recovery_note="Review the lock file before retrying daemon-start.",
                manual_review_required=True,
                operation_id=operation_id,
                include_event_record=include_event_record,
            ),
        ) from exc

    process = _spawn_daemon_subprocess(command, status.log_path)
    status.pid_path.write_text(f"{process.pid}\n", encoding="utf-8")
    if not _wait_for_bridge_health(status.health_url, wait_seconds=wait_seconds):
        _signal_process(process.pid, signal.SIGTERM)
        _remove_file_if_exists(status.pid_path)
        _remove_file_if_exists(status.lock_path)
        raise ResidentDaemonProcessControlError(
            "resident daemon failed readiness check",
            payload=_build_control_receipt(
                operation="start",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=ResidentDaemonState.FAILED,
                result="failed",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                pid=process.pid,
                failure_mode="readiness_timeout",
                recovery_note="Inspect the log file before retrying daemon-start.",
                command=tuple(command),
                operation_id=operation_id,
                include_event_record=include_event_record,
            ),
        )

    return _build_control_receipt(
        operation="start",
        runtime_root=runtime_root,
        host=host,
        port=port,
        state_before=status.state,
        state_after=ResidentDaemonState.RUNNING,
        result="started",
        applied=True,
        pid_path=status.pid_path,
        lock_path=status.lock_path,
        log_path=status.log_path,
        health_url=status.health_url,
        pid=process.pid,
        recovery_note="Use daemon-stop for graceful shutdown.",
        command=tuple(command),
        operation_id=operation_id,
        include_event_record=include_event_record,
    )


def stop_resident_daemon(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    wait_seconds: float = 5.0,
    include_event_record: bool = False,
) -> dict[str, Any]:
    """Stop a minimal local-only resident daemon subprocess."""
    status = build_daemon_status_report(runtime_root, host=host, port=port)
    if status.manual_review_required:
        raise ResidentDaemonProcessControlError(
            "resident daemon stop requires manual review",
            payload=_build_control_receipt(
                operation="stop",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=status.state,
                result="requires_review",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                pid=status.pid,
                failure_mode=status.failure_mode,
                recovery_note="Review stale runtime artifacts before daemon-stop.",
                manual_review_required=True,
                include_event_record=include_event_record,
            ),
        )
    if status.pid is None:
        return _build_control_receipt(
            operation="stop",
            runtime_root=runtime_root,
            host=host,
            port=port,
            state_before=status.state,
            state_after=ResidentDaemonState.STOPPED,
            result="no_action",
            applied=False,
            pid_path=status.pid_path,
            lock_path=status.lock_path,
            log_path=status.log_path,
            health_url=status.health_url,
            recovery_note="No running resident daemon was found.",
            include_event_record=include_event_record,
        )

    _signal_process(status.pid, signal.SIGTERM)
    if not _wait_for_process_exit(status.pid, wait_seconds=wait_seconds):
        raise ResidentDaemonProcessControlError(
            "resident daemon stop timed out",
            payload=_build_control_receipt(
                operation="stop",
                runtime_root=runtime_root,
                host=host,
                port=port,
                state_before=status.state,
                state_after=ResidentDaemonState.STOPPING,
                result="failed",
                applied=False,
                pid_path=status.pid_path,
                lock_path=status.lock_path,
                log_path=status.log_path,
                health_url=status.health_url,
                pid=status.pid,
                failure_mode="stop_timeout",
                recovery_note="Inspect the process manually before retrying daemon-stop.",
                include_event_record=include_event_record,
            ),
        )
    _remove_file_if_exists(status.pid_path)
    _remove_file_if_exists(status.lock_path)
    return _build_control_receipt(
        operation="stop",
        runtime_root=runtime_root,
        host=host,
        port=port,
        state_before=status.state,
        state_after=ResidentDaemonState.STOPPED,
        result="stopped",
        applied=True,
        pid_path=status.pid_path,
        lock_path=status.lock_path,
        log_path=status.log_path,
        health_url=status.health_url,
        pid=status.pid,
        recovery_note="Resident daemon stopped and runtime control files were removed.",
        include_event_record=include_event_record,
    )


def restart_resident_daemon(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    wait_seconds: float = 5.0,
    include_event_record: bool = False,
) -> dict[str, Any]:
    """Restart a minimal local-only resident daemon subprocess."""
    stop_receipt = stop_resident_daemon(
        runtime_root,
        host=host,
        port=port,
        wait_seconds=wait_seconds,
        include_event_record=False,
    )
    start_receipt = start_resident_daemon(
        runtime_root,
        host=host,
        port=port,
        wait_seconds=wait_seconds,
        include_event_record=False,
    )
    start_receipt["kind"] = "resident_daemon_process_control_receipt"
    start_receipt["operation"] = "restart"
    start_receipt["result"] = "restarted"
    start_receipt["state_before"] = stop_receipt["state_before"]
    start_receipt["recovery_note"] = "Resident daemon was stopped and started again."
    start_receipt["stop_result"] = stop_receipt["result"]
    if include_event_record:
        from sayane.app.daemon_event_records import build_process_control_event_record

        start_receipt["event_record"] = build_process_control_event_record(
            operation_id=start_receipt["operation_id"],
            operation="restart",
            runtime_root=runtime_root,
            result="restarted",
            state_before=start_receipt["state_before"],
            state_after=start_receipt["state_after"],
            host=host,
            port=port,
            pid=start_receipt.get("pid"),
            applied=True,
        ).public_metadata()
    return start_receipt
