"""Resident daemon runtime initialization metadata schema."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonRuntimeInitMetadata:
    """Initial runtime metadata placeholder.

    This metadata is initialization-only and must not be treated as daemon
    liveness, readiness, ownership, or process identity proof.
    """

    runtime_root: Path
    operation_id: str
    creator_surface: str
    write_metadata_requested: bool = True
    confirm_operation_id: str | None = None
    confirmation_matched: bool = False
    schema_version: str = "1"
    disclaimer: str = (
        "Initialization metadata only; not daemon liveness, readiness, ownership, "
        "or process identity proof."
    )
    created_at: str | None = None

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_runtime_init_metadata",
            "schema_version": self.schema_version,
            "runtime_root": str(self.runtime_root),
            "operation_id": self.operation_id,
            "creator_surface": self.creator_surface,
            "write_metadata_requested": self.write_metadata_requested,
            "confirm_operation_id": self.confirm_operation_id,
            "confirmation_matched": self.confirmation_matched,
            "created_at": self.created_at or datetime.now(UTC).isoformat(),
            "disclaimer": self.disclaimer,
        }


def build_runtime_init_metadata(
    *,
    runtime_root: Path,
    operation_id: str,
    creator_surface: str,
    write_metadata_requested: bool = True,
    confirm_operation_id: str | None = None,
    confirmation_matched: bool = False,
) -> ResidentDaemonRuntimeInitMetadata:
    """Build initialization metadata placeholder."""
    return ResidentDaemonRuntimeInitMetadata(
        runtime_root=runtime_root,
        operation_id=operation_id,
        creator_surface=creator_surface,
        write_metadata_requested=write_metadata_requested,
        confirm_operation_id=confirm_operation_id,
        confirmation_matched=confirmation_matched,
    )
