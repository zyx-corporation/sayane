"""Tests for resident daemon stale artifact diagnostics (#199)."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonArtifactStatus,
    ResidentDaemonIdentity,
    ResidentDaemonRuntimeLayout,
    build_stale_artifact_report,
)


def test_stale_artifact_report_is_read_only_when_artifacts_are_missing(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)

    report = build_stale_artifact_report(identity=identity, layout=layout)
    payload = report.public_metadata()

    assert payload["kind"] == "resident_daemon_stale_artifact_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["stale_artifact_policy"] == "manual_review_required"
    assert payload["repairs_artifacts"] is False
    assert payload["deletes_artifacts"] is False
    assert payload["creates_artifacts"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["manual_review_required"] is False
    assert len(payload["diagnostics"]) == 10
    assert all(
        diagnostic["status"] == ResidentDaemonArtifactStatus.MISSING.value
        for diagnostic in payload["diagnostics"]
    )
    assert runtime_root.exists() is False


def test_stale_artifact_report_requires_review_for_existing_pid_file(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)

    report = build_stale_artifact_report(identity=identity, layout=layout)
    payload = report.public_metadata()

    pid_diagnostic = next(
        diagnostic for diagnostic in payload["diagnostics"] if diagnostic["kind"] == "pid_file"
    )
    assert pid_diagnostic["exists"] is True
    assert pid_diagnostic["is_file"] is True
    assert pid_diagnostic["status"] == "present_review_required"
    assert pid_diagnostic["manual_review_required"] is True
    assert pid_diagnostic["safe_to_delete"] is False
    assert pid_path.exists() is True


def test_stale_artifact_report_flags_type_mismatch_for_socket_path(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    socket_path = runtime_root / "sayane-resident.sock"
    socket_path.write_text("not a socket\n", encoding="utf-8")
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)

    report = build_stale_artifact_report(identity=identity, layout=layout)
    payload = report.public_metadata()

    socket_diagnostic = next(
        diagnostic for diagnostic in payload["diagnostics"] if diagnostic["kind"] == "socket_file"
    )
    assert socket_diagnostic["exists"] is True
    assert socket_diagnostic["is_socket"] is False
    assert socket_diagnostic["status"] == "type_mismatch_review_required"
    assert socket_diagnostic["manual_review_required"] is True
    assert socket_diagnostic["safe_to_delete"] is False
    assert socket_path.exists() is True
