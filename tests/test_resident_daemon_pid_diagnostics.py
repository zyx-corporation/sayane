"""Tests for resident daemon PID file parse diagnostics (#202)."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonIdentity,
    ResidentDaemonPidParseStatus,
    build_pid_file_diagnostic,
)


def test_pid_file_diagnostic_reports_missing_without_review(tmp_path: Path) -> None:
    identity = ResidentDaemonIdentity(runtime_dir=tmp_path / "run")

    payload = build_pid_file_diagnostic(identity).public_metadata()

    assert payload["kind"] == "resident_daemon_pid_file_parse_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["exists"] is False
    assert payload["status"] == ResidentDaemonPidParseStatus.MISSING.value
    assert payload["parsed_pid"] is None
    assert payload["manual_review_required"] is False
    assert payload["proves_liveness"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["mutates_filesystem"] is False


def test_pid_file_diagnostic_reports_empty_with_review(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("\n", encoding="utf-8")

    payload = build_pid_file_diagnostic(identity).public_metadata()

    assert payload["exists"] is True
    assert payload["status"] == ResidentDaemonPidParseStatus.EMPTY.value
    assert payload["parsed_pid"] is None
    assert payload["manual_review_required"] is True
    assert payload["proves_liveness"] is False
    assert identity.pid_path.exists() is True


def test_pid_file_diagnostic_reports_invalid_with_review(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("not-a-pid\n", encoding="utf-8")

    payload = build_pid_file_diagnostic(identity).public_metadata()

    assert payload["exists"] is True
    assert payload["status"] == ResidentDaemonPidParseStatus.INVALID.value
    assert payload["parsed_pid"] is None
    assert payload["raw_value_preview"] == "not-a-pid\\n"
    assert payload["manual_review_required"] is True
    assert payload["controls_process"] is False


def test_pid_file_diagnostic_reports_parsed_pid_without_liveness_proof(
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("12345\n", encoding="utf-8")

    payload = build_pid_file_diagnostic(identity).public_metadata()

    assert payload["exists"] is True
    assert payload["status"] == ResidentDaemonPidParseStatus.PARSED.value
    assert payload["parsed_pid"] == 12345
    assert payload["raw_value_preview"] == "12345\\n"
    assert payload["manual_review_required"] is True
    assert payload["proves_liveness"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["mutates_filesystem"] is False
