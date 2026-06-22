"""Tests for resident daemon runtime init receipts."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_runtime_init_receipt


def test_runtime_init_receipt_public_metadata_is_non_persistent(tmp_path: Path) -> None:
    payload = build_runtime_init_receipt(
        runtime_root=tmp_path / "run",
        operation_id="receipt-001",
        creator_surface="daemon-runtime-init",
        plan_fingerprint="abcd1234abcd1234",
        applied=True,
        result="applied",
        created_paths=(str(tmp_path / "run"), str(tmp_path / "run" / "state")),
        mutations_performed=(
            str(tmp_path / "run"),
            str(tmp_path / "run" / "state"),
            str(tmp_path / "run" / "state" / "runtime-init.json"),
        ),
        metadata_written=True,
        metadata_path=str(tmp_path / "run" / "state" / "runtime-init.json"),
        confirm_operation_id="receipt-001",
        confirm_plan_fingerprint="abcd1234abcd1234",
        confirmation_matched=True,
        fingerprint_matched=True,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_runtime_init_receipt"
    assert payload["schema_version"] == "1"
    assert payload["runtime_root"] == str(tmp_path / "run")
    assert payload["operation_id"] == "receipt-001"
    assert payload["plan_fingerprint"] == "abcd1234abcd1234"
    assert payload["applied"] is True
    assert payload["result"] == "applied"
    assert payload["metadata_written"] is True
    assert payload["failure_mode"] is None
    assert payload["metadata_path"] == str(tmp_path / "run" / "state" / "runtime-init.json")
    assert payload["confirm_operation_id"] == "receipt-001"
    assert payload["confirm_plan_fingerprint"] == "abcd1234abcd1234"
    assert payload["confirmation_matched"] is True
    assert payload["fingerprint_matched"] is True
    assert payload["persisted"] is False
    assert "not persistent audit storage" in payload["disclaimer"].lower()
