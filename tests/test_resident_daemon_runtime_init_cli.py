"""Tests for resident daemon runtime init CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


def test_daemon_runtime_init_json_preview_does_not_create_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-runtime-init", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_runtime_init_plan"
    assert payload["operation_id"].startswith("runtime-init-")
    assert len(payload["plan_fingerprint"]) == 16
    assert payload["preview_only"] is True
    assert payload["mutates_filesystem"] is False
    assert payload["review_required"] is False
    assert runtime_root.exists() is False


def test_daemon_runtime_init_preview_can_include_event_record(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--include-event-record",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["event_record"]["kind"] == "resident_daemon_event_record"
    assert payload["event_record"]["category"] == "preview"
    assert payload["event_record"]["surface"] == "daemon-runtime-init"


def test_daemon_runtime_init_apply_creates_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--operation-id",
            "cli-op-1",
            "--include-event-record",
            "--apply",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_runtime_init_apply"
    assert payload["operation_id"] == "cli-op-1"
    assert payload["applied"] is True
    assert payload["result"] == "applied"
    assert payload["event_record"]["category"] == "apply"
    assert payload["event_record"]["result"] == "succeeded"
    assert payload["event_record"]["consent"] == "required"
    assert payload["receipt"]["kind"] == "resident_daemon_runtime_init_receipt"
    assert payload["receipt"]["result"] == "applied"
    assert payload["metadata_written"] is False
    assert len(payload["created_paths"]) == 7
    assert (runtime_root / "state").is_dir()


def test_daemon_runtime_init_apply_can_write_metadata(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    preview = runner.invoke(
        app,
        ["app", "daemon-runtime-init", "--runtime-root", str(runtime_root), "--json"],
    )
    preview_payload = json.loads(preview.stdout)
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--operation-id",
            "cli-meta-1",
            "--confirm-operation-id",
            "cli-meta-1",
            "--confirm-plan-fingerprint",
            preview_payload["plan_fingerprint"],
            "--apply",
            "--write-metadata",
            "--include-event-record",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["metadata_written"] is True
    assert payload["confirmation_matched"] is True
    assert payload["metadata"]["operation_id"] == "cli-meta-1"
    assert payload["metadata"]["plan_fingerprint"] == preview_payload["plan_fingerprint"]
    assert payload["metadata"]["confirm_operation_id"] == "cli-meta-1"
    assert payload["metadata"]["confirm_plan_fingerprint"] == preview_payload["plan_fingerprint"]
    assert payload["metadata"]["confirmation_matched"] is True
    assert payload["metadata"]["fingerprint_matched"] is True
    assert payload["receipt"]["metadata_written"] is True
    assert payload["receipt"]["metadata_path"] == str(runtime_root / "state" / "runtime-init.json")
    assert payload["receipt"]["confirm_operation_id"] == "cli-meta-1"
    assert payload["receipt"]["confirm_plan_fingerprint"] == preview_payload["plan_fingerprint"]
    assert payload["fingerprint_matched"] is True
    assert payload["event_record"]["consent"] == "operator_apply_and_confirm_required"
    assert "confirm_operation_id:cli-meta-1" in payload["event_record"]["evidence"]
    assert (
        f"plan_fingerprint:{preview_payload['plan_fingerprint']}"
        in payload["event_record"]["evidence"]
    )
    assert (runtime_root / "state" / "runtime-init.json").is_file()


def test_daemon_runtime_init_apply_rejects_metadata_without_confirmation(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--operation-id",
            "cli-meta-2",
            "--apply",
            "--write-metadata",
        ],
    )

    assert result.exit_code != 0
    combined = result.stdout + (result.stderr or "")
    assert "confirm_operation_id" in combined


def test_daemon_runtime_init_apply_json_reports_structured_confirmation_failure(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--operation-id",
            "cli-meta-3",
            "--apply",
            "--write-metadata",
            "--include-event-record",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["result"] == "aborted"
    assert payload["failure_mode"] == "confirm_operation_id_missing"
    assert payload["event_record"]["category"] == "apply"
    assert payload["event_record"]["result"] == "failed"
    assert payload["receipt"]["applied"] is False


def test_daemon_runtime_init_apply_rejects_conflicting_paths(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "pid").write_text("conflict", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--apply",
        ],
    )

    assert result.exit_code != 0
    combined = result.stdout + (result.stderr or "")
    assert "manual review" in combined.lower()


def test_daemon_runtime_init_apply_json_reports_structured_manual_review(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "pid").write_text("conflict", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--apply",
            "--include-event-record",
            "--json",
        ],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["result"] == "requires_review"
    assert payload["failure_mode"] == "manual_review_required"
    assert payload["event_record"]["category"] == "apply"
    assert payload["event_record"]["result"] == "requires_review"
