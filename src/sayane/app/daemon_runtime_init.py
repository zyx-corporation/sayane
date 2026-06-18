"""Minimal resident daemon runtime initialization.

This module implements the smallest approved mutation slice for the future
resident daemon: explicit creation of an empty runtime root and its planned
subdirectories. It does not write PID files, metadata, sockets, or locks.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout


class ResidentDaemonRuntimeInitStatus(StrEnum):
    """Conservative runtime init item statuses."""

    CREATE = "create"
    NO_ACTION = "no_action"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


@dataclass(frozen=True)
class ResidentDaemonRuntimeInitItem:
    """One runtime init target path decision."""

    path: Path
    path_role: str
    status: ResidentDaemonRuntimeInitStatus
    reason: str

    def public_metadata(self) -> dict[str, str]:
        return {
            "path": str(self.path),
            "path_role": self.path_role,
            "status": self.status.value,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class ResidentDaemonRuntimeInitPlan:
    """Explicit runtime initialization preview/apply plan."""

    runtime_root: Path
    items: tuple[ResidentDaemonRuntimeInitItem, ...]
    operation_id: str
    creator_surface: str = "daemon-runtime-init"
    explicit_operator_intent_required: bool = True

    @property
    def review_required(self) -> bool:
        return any(
            item.status is ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED
            for item in self.items
        )

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_runtime_init_plan",
            "operation_id": self.operation_id,
            "creator_surface": self.creator_surface,
            "runtime_root": str(self.runtime_root),
            "review_required": self.review_required,
            "explicit_operator_intent_required": self.explicit_operator_intent_required,
            "items": [item.public_metadata() for item in self.items],
            "target_paths": [str(item.path) for item in self.items],
            "prior_state": [item.public_metadata() for item in self.items],
            "proposed_state": {
                "create_paths": [
                    str(item.path)
                    for item in self.items
                    if item.status is ResidentDaemonRuntimeInitStatus.CREATE
                ],
                "no_action_paths": [
                    str(item.path)
                    for item in self.items
                    if item.status is ResidentDaemonRuntimeInitStatus.NO_ACTION
                ],
                "manual_review_paths": [
                    str(item.path)
                    for item in self.items
                    if item.status is ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED
                ],
            },
            "creates_directories": True,
            "writes_files": False,
            "writes_pid_file": False,
            "creates_socket": False,
            "acquires_lock": False,
            "starts_daemon": False,
            "operator_confirmation_signal": "--apply",
        }


def _classify_directory_target(path: Path, *, path_role: str) -> ResidentDaemonRuntimeInitItem:
    if path.exists():
        if path.is_symlink():
            return ResidentDaemonRuntimeInitItem(
                path=path,
                path_role=path_role,
                status=ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED,
                reason="existing symlink requires manual review",
            )
        if path.is_dir():
            return ResidentDaemonRuntimeInitItem(
                path=path,
                path_role=path_role,
                status=ResidentDaemonRuntimeInitStatus.NO_ACTION,
                reason="directory already exists",
            )
        return ResidentDaemonRuntimeInitItem(
            path=path,
            path_role=path_role,
            status=ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED,
            reason="conflicting non-directory path requires manual review",
        )
    return ResidentDaemonRuntimeInitItem(
        path=path,
        path_role=path_role,
        status=ResidentDaemonRuntimeInitStatus.CREATE,
        reason="missing directory may be created with explicit apply intent",
    )


def build_runtime_init_plan(
    runtime_root: Path,
    *,
    operation_id: str | None = None,
    creator_surface: str = "daemon-runtime-init",
) -> ResidentDaemonRuntimeInitPlan:
    """Build an explicit runtime initialization plan."""
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    items = (
        _classify_directory_target(layout.runtime_root, path_role="runtime_root"),
        _classify_directory_target(layout.pid_dir, path_role="pid_dir"),
        _classify_directory_target(layout.lock_dir, path_role="lock_dir"),
        _classify_directory_target(layout.socket_dir, path_role="socket_dir"),
        _classify_directory_target(layout.log_dir, path_role="log_dir"),
        _classify_directory_target(layout.temp_dir, path_role="temp_dir"),
        _classify_directory_target(layout.state_dir, path_role="state_dir"),
    )
    return ResidentDaemonRuntimeInitPlan(
        runtime_root=runtime_root,
        items=items,
        operation_id=operation_id or f"runtime-init-{uuid4().hex[:12]}",
        creator_surface=creator_surface,
    )


def apply_runtime_init(plan: ResidentDaemonRuntimeInitPlan) -> dict[str, Any]:
    """Apply a runtime initialization plan."""
    if plan.review_required:
        msg = "runtime init plan requires manual review before apply"
        raise ValueError(msg)

    created_paths: list[str] = []
    for item in plan.items:
        if item.status is ResidentDaemonRuntimeInitStatus.CREATE:
            item.path.mkdir(parents=True, exist_ok=False)
            created_paths.append(str(item.path))

    payload = plan.public_metadata()
    payload.update(
        {
            "kind": "resident_daemon_runtime_init_apply",
            "applied": True,
            "created_paths": created_paths,
            "mutations_performed": created_paths,
            "mutates_filesystem": True,
            "result": "applied" if created_paths else "no_action",
            "failure_mode": None,
            "recovery_note": (
                "No rollback performed; directories created explicitly under runtime_root."
            ),
        },
    )
    return payload
