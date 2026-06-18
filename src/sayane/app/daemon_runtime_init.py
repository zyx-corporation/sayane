"""Minimal resident daemon runtime initialization.

This module implements the smallest approved mutation slice for the future
resident daemon: explicit creation of an empty runtime root and its planned
subdirectories. It does not write PID files, metadata, sockets, or locks.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.app.daemon_runtime_layout import ResidentDaemonRuntimeLayout
from sayane.app.daemon_runtime_metadata import build_runtime_init_metadata


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
    metadata_filename: str = "runtime-init.json"

    @property
    def review_required(self) -> bool:
        return any(
            item.status is ResidentDaemonRuntimeInitStatus.MANUAL_REVIEW_REQUIRED
            for item in self.items
        )

    def plan_fingerprint(self) -> str:
        basis = {
            "creator_surface": self.creator_surface,
            "runtime_root": str(self.runtime_root),
            "items": [item.public_metadata() for item in self.items],
            "metadata_filename": self.metadata_filename,
        }
        encoded = json.dumps(basis, ensure_ascii=False, sort_keys=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()[:16]

    def public_metadata(self) -> dict[str, Any]:
        metadata_path = self.runtime_root / "state" / self.metadata_filename
        return {
            "kind": "resident_daemon_runtime_init_plan",
            "operation_id": self.operation_id,
            "plan_fingerprint": self.plan_fingerprint(),
            "creator_surface": self.creator_surface,
            "runtime_root": str(self.runtime_root),
            "review_required": self.review_required,
            "explicit_operator_intent_required": self.explicit_operator_intent_required,
            "items": [item.public_metadata() for item in self.items],
            "target_paths": [str(item.path) for item in self.items],
            "metadata_path": str(metadata_path),
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
                "metadata_placeholder": build_runtime_init_metadata(
                    runtime_root=self.runtime_root,
                    operation_id=self.operation_id,
                    creator_surface=self.creator_surface,
                    write_metadata_requested=False,
                    confirm_operation_id=None,
                    confirmation_matched=False,
                ).public_metadata(),
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


def apply_runtime_init(
    plan: ResidentDaemonRuntimeInitPlan,
    *,
    include_event_record: bool = False,
    write_metadata: bool = False,
    confirm_operation_id: str | None = None,
    confirm_plan_fingerprint: str | None = None,
) -> dict[str, Any]:
    """Apply a runtime initialization plan."""
    if plan.review_required:
        msg = "runtime init plan requires manual review before apply"
        raise ValueError(msg)
    if write_metadata and confirm_operation_id is None:
        msg = "write_metadata requires explicit confirm_operation_id"
        raise ValueError(msg)
    if confirm_operation_id is not None and confirm_operation_id != plan.operation_id:
        msg = "confirm_operation_id must match the plan operation_id"
        raise ValueError(msg)
    if confirm_plan_fingerprint is not None and confirm_plan_fingerprint != plan.plan_fingerprint():
        msg = "confirm_plan_fingerprint must match the plan fingerprint"
        raise ValueError(msg)
    if write_metadata and confirm_plan_fingerprint is None:
        msg = "write_metadata requires explicit confirm_plan_fingerprint"
        raise ValueError(msg)

    created_paths: list[str] = []
    for item in plan.items:
        if item.status is ResidentDaemonRuntimeInitStatus.CREATE:
            item.path.mkdir(parents=True, exist_ok=False)
            created_paths.append(str(item.path))

    payload = plan.public_metadata()
    metadata_path = plan.runtime_root / "state" / plan.metadata_filename
    payload.update(
        {
            "kind": "resident_daemon_runtime_init_apply",
            "applied": True,
            "plan_fingerprint": plan.plan_fingerprint(),
            "created_paths": created_paths,
            "mutations_performed": created_paths,
            "mutates_filesystem": True,
            "result": "applied" if created_paths else "no_action",
            "failure_mode": None,
            "recovery_note": (
                "No rollback performed; directories created explicitly under runtime_root."
            ),
            "write_metadata_requested": write_metadata,
            "confirm_operation_id": confirm_operation_id,
            "confirm_plan_fingerprint": confirm_plan_fingerprint,
            "confirmation_matched": confirm_operation_id == plan.operation_id
            if confirm_operation_id is not None
            else False,
            "fingerprint_matched": confirm_plan_fingerprint == plan.plan_fingerprint()
            if confirm_plan_fingerprint is not None
            else False,
        },
    )
    if write_metadata:
        metadata_payload = build_runtime_init_metadata(
            runtime_root=plan.runtime_root,
            operation_id=plan.operation_id,
            creator_surface=plan.creator_surface,
            write_metadata_requested=True,
            confirm_operation_id=confirm_operation_id,
            confirmation_matched=payload["confirmation_matched"],
        ).public_metadata()
        metadata_path.write_text(
            __import__("json").dumps(metadata_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        payload["metadata_written"] = True
        payload["metadata_path"] = str(metadata_path)
        payload["metadata"] = metadata_payload
        payload["mutations_performed"] = [*created_paths, str(metadata_path)]
    else:
        payload["metadata_written"] = False
    if include_event_record:
        from sayane.app.daemon_event_records import build_runtime_init_event_record

        payload["event_record"] = build_runtime_init_event_record(
            plan,
            applied=True,
            created_paths=tuple(payload["mutations_performed"]),
            write_metadata=write_metadata,
            confirm_operation_id=confirm_operation_id,
            confirmation_matched=payload["confirmation_matched"],
        ).public_metadata()
    return payload
