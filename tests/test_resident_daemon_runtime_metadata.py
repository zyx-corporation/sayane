"""Tests for resident daemon runtime init metadata schema."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_runtime_init_metadata


def test_runtime_init_metadata_public_metadata_is_non_liveness_placeholder(
    tmp_path: Path,
) -> None:
    payload = build_runtime_init_metadata(
        runtime_root=tmp_path / "run",
        operation_id="meta-001",
        creator_surface="daemon-runtime-init",
        write_metadata_requested=True,
        confirm_operation_id="meta-001",
        confirmation_matched=True,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_runtime_init_metadata"
    assert payload["schema_version"] == "1"
    assert payload["runtime_root"] == str(tmp_path / "run")
    assert payload["operation_id"] == "meta-001"
    assert payload["write_metadata_requested"] is True
    assert payload["confirm_operation_id"] == "meta-001"
    assert payload["confirmation_matched"] is True
    assert "not daemon liveness" in payload["disclaimer"].lower()
