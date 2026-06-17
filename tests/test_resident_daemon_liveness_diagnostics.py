"""Tests for resident daemon liveness diagnostic preview (#207)."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonIdentity,
    ResidentDaemonLivenessStatus,
    ResidentDaemonPidFileDiagnostic,
    ResidentDaemonPidParseStatus,
    build_liveness_diagnostic,
    build_liveness_diagnostic_from_pid_file_diagnostic,
)


def test_liveness_diagnostic_reports_missing_pid_as_unverified(tmp_path: Path) -> None:
    identity = ResidentDaemonIdentity(runtime_dir=tmp_path / "run")

    payload = build_liveness_diagnostic(identity).public_metadata()

    assert payload["kind"] == "resident_daemon_liveness_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["status"] == ResidentDaemonLivenessStatus.PID_MISSING_LIVENESS_UNVERIFIED.value
    assert payload["evidence_ceiling"] == "pid_file_diagnostic_only"
    assert payload["manual_review_required"] is False
    assert payload["proves_liveness"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["pid_file"]["status"] == ResidentDaemonPidParseStatus.MISSING.value


def test_liveness_diagnostic_maps_unreadable_pid_to_unverified(tmp_path: Path) -> None:
    pid_diagnostic = ResidentDaemonPidFileDiagnostic(
        path=tmp_path / "sayane-resident.pid",
        exists=True,
        status=ResidentDaemonPidParseStatus.UNREADABLE,
        error="PermissionError: denied",
        manual_review_required=True,
    )

    payload = build_liveness_diagnostic_from_pid_file_diagnostic(pid_diagnostic).public_metadata()

    assert payload["status"] == ResidentDaemonLivenessStatus.PID_UNREADABLE_LIVENESS_UNVERIFIED.value
    assert payload["evidence_ceiling"] == "pid_file_diagnostic_only"
    assert payload["manual_review_required"] is True
    assert payload["proves_liveness"] is False
    assert payload["pid_file"]["status"] == ResidentDaemonPidParseStatus.UNREADABLE.value


def test_liveness_diagnostic_maps_empty_pid_to_unverified(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("\n", encoding="utf-8")

    payload = build_liveness_diagnostic(identity).public_metadata()

    assert payload["status"] == ResidentDaemonLivenessStatus.PID_EMPTY_LIVENESS_UNVERIFIED.value
    assert payload["manual_review_required"] is True
    assert payload["probes_process"] is False
    assert payload["pid_file"]["status"] == ResidentDaemonPidParseStatus.EMPTY.value


def test_liveness_diagnostic_maps_invalid_pid_to_unverified(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("not-a-pid\n", encoding="utf-8")

    payload = build_liveness_diagnostic(identity).public_metadata()

    assert payload["status"] == ResidentDaemonLivenessStatus.PID_INVALID_LIVENESS_UNVERIFIED.value
    assert payload["manual_review_required"] is True
    assert payload["controls_process"] is False
    assert payload["pid_file"]["status"] == ResidentDaemonPidParseStatus.INVALID.value


def test_liveness_diagnostic_maps_parsed_pid_to_process_unverified(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "run"
    runtime_dir.mkdir()
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir)
    identity.pid_path.write_text("12345\n", encoding="utf-8")

    payload = build_liveness_diagnostic(identity).public_metadata()

    assert payload["status"] == ResidentDaemonLivenessStatus.PID_PARSED_PROCESS_UNVERIFIED.value
    assert payload["evidence_ceiling"] == "pid_file_parsed_only"
    assert payload["manual_review_required"] is True
    assert payload["proves_liveness"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["pid_file"]["status"] == ResidentDaemonPidParseStatus.PARSED.value
    assert payload["pid_file"]["parsed_pid"] == 12345
