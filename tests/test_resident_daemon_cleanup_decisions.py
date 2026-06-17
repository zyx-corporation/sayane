"""Tests for resident daemon cleanup decision model (#200)."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonCleanupRecommendation,
    ResidentDaemonIdentity,
    ResidentDaemonRuntimeLayout,
    build_cleanup_decision_report,
    build_stale_artifact_report,
)


def _report(runtime_root: Path):
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root)
    stale_report = build_stale_artifact_report(identity=identity, layout=layout)
    return build_cleanup_decision_report(stale_report).public_metadata()


def test_cleanup_decision_report_is_no_action_for_missing_artifacts(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"

    payload = _report(runtime_root)

    assert payload["kind"] == "resident_daemon_cleanup_decision_preview"
    assert payload["preview_only"] is True
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["decision_policy"] == "manual_review_required"
    assert payload["deletes_artifacts"] is False
    assert payload["repairs_artifacts"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["manual_review_required"] is False
    assert len(payload["decisions"]) == 10
    assert all(
        decision["recommendation"]
        == ResidentDaemonCleanupRecommendation.NO_ACTION.value
        for decision in payload["decisions"]
    )
    assert runtime_root.exists() is False


def test_cleanup_decision_report_requires_review_for_present_pid_file(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    payload = _report(runtime_root)

    pid_decision = next(
        decision for decision in payload["decisions"] if decision["artifact_kind"] == "pid_file"
    )
    assert payload["manual_review_required"] is True
    assert pid_decision["recommendation"] == "manual_review_required"
    assert pid_decision["manual_review_required"] is True
    assert pid_decision["safe_to_delete"] is False
    assert pid_decision["deletes_artifact"] is False
    assert pid_decision["mutates_filesystem"] is False
    assert pid_path.exists() is True


def test_cleanup_decision_report_marks_type_mismatch_unsafe_to_delete(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    runtime_root.mkdir()
    socket_path = runtime_root / "sayane-resident.sock"
    socket_path.write_text("not a socket\n", encoding="utf-8")

    payload = _report(runtime_root)

    socket_decision = next(
        decision
        for decision in payload["decisions"]
        if decision["artifact_kind"] == "socket_file"
    )
    assert socket_decision["diagnostic_status"] == "type_mismatch_review_required"
    assert socket_decision["recommendation"] == "unsafe_to_delete"
    assert socket_decision["manual_review_required"] is True
    assert socket_decision["safe_to_delete"] is False
    assert socket_decision["deletes_artifact"] is False
    assert socket_path.exists() is True
