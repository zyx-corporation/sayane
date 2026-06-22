"""Resident daemon runtime initialization receipt schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonRuntimeInitReceipt:
    """Non-persistent apply receipt for runtime initialization."""

    runtime_root: Path
    operation_id: str
    creator_surface: str
    plan_fingerprint: str
    applied: bool
    result: str
    created_paths: tuple[str, ...]
    mutations_performed: tuple[str, ...]
    metadata_written: bool
    failure_mode: str | None = None
    recovery_note: str | None = None
    metadata_path: str | None = None
    confirm_operation_id: str | None = None
    confirm_plan_fingerprint: str | None = None
    confirmation_matched: bool = False
    fingerprint_matched: bool = False
    schema_version: str = "1"
    disclaimer: str = (
        "Apply receipt only; not persistent audit storage, daemon liveness, readiness, "
        "ownership, or process identity proof."
    )
    created_at: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_runtime_init_receipt",
            "schema_version": self.schema_version,
            "runtime_root": str(self.runtime_root),
            "operation_id": self.operation_id,
            "creator_surface": self.creator_surface,
            "plan_fingerprint": self.plan_fingerprint,
            "applied": self.applied,
            "result": self.result,
            "created_paths": list(self.created_paths),
            "mutations_performed": list(self.mutations_performed),
            "metadata_written": self.metadata_written,
            "failure_mode": self.failure_mode,
            "recovery_note": self.recovery_note,
            "metadata_path": self.metadata_path,
            "confirm_operation_id": self.confirm_operation_id,
            "confirm_plan_fingerprint": self.confirm_plan_fingerprint,
            "confirmation_matched": self.confirmation_matched,
            "fingerprint_matched": self.fingerprint_matched,
            "created_at": self.created_at or datetime.now(UTC).isoformat(),
            "disclaimer": self.disclaimer,
            "persisted": False,
        }


def build_runtime_init_receipt(
    *,
    runtime_root: Path,
    operation_id: str,
    creator_surface: str,
    plan_fingerprint: str,
    applied: bool,
    result: str,
    created_paths: tuple[str, ...],
    mutations_performed: tuple[str, ...],
    metadata_written: bool,
    failure_mode: str | None = None,
    recovery_note: str | None = None,
    metadata_path: str | None = None,
    confirm_operation_id: str | None = None,
    confirm_plan_fingerprint: str | None = None,
    confirmation_matched: bool = False,
    fingerprint_matched: bool = False,
) -> ResidentDaemonRuntimeInitReceipt:
    """Build a non-persistent runtime-init apply receipt."""
    return ResidentDaemonRuntimeInitReceipt(
        runtime_root=runtime_root,
        operation_id=operation_id,
        creator_surface=creator_surface,
        plan_fingerprint=plan_fingerprint,
        applied=applied,
        result=result,
        created_paths=created_paths,
        mutations_performed=mutations_performed,
        metadata_written=metadata_written,
        failure_mode=failure_mode,
        recovery_note=recovery_note,
        metadata_path=metadata_path,
        confirm_operation_id=confirm_operation_id,
        confirm_plan_fingerprint=confirm_plan_fingerprint,
        confirmation_matched=confirmation_matched,
        fingerprint_matched=fingerprint_matched,
    )
