"""Tests for resident daemon readiness diagnostic preview."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonApiReadinessStatus,
    ResidentDaemonReadinessStatus,
    build_daemon_status_report,
    build_readiness_diagnostic,
    build_readiness_diagnostic_from_status_report,
    build_runtime_init_plan,
)
from sayane.app.daemon_runtime_init import apply_runtime_init


def test_readiness_diagnostic_reports_stopped_daemon_as_not_ready(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"

    payload = build_readiness_diagnostic(runtime_root).public_metadata()

    assert payload["kind"] == "resident_daemon_readiness_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["readiness_status"] == ResidentDaemonReadinessStatus.READINESS_NOT_READY.value
    assert payload["api_readiness_status"] == ResidentDaemonApiReadinessStatus.API_UNREACHABLE.value
    assert payload["evidence_ceiling"] == "no_running_process"
    assert payload["proves_daemon_readiness"] is False
    assert payload["proves_api_readiness"] is False
    assert payload["probes_process"] is True
    assert payload["probes_api"] is True


def test_readiness_diagnostic_reports_manual_review_when_status_is_ambiguous(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    (runtime_root / "sayane-resident.pid").write_text("12345\n", encoding="utf-8")

    payload = build_readiness_diagnostic(runtime_root).public_metadata()

    assert payload["readiness_status"] == ResidentDaemonReadinessStatus.MANUAL_REVIEW_REQUIRED.value
    assert (
        payload["api_readiness_status"]
        == ResidentDaemonApiReadinessStatus.MANUAL_REVIEW_REQUIRED.value
    )
    assert payload["manual_review_required"] is True


def test_readiness_diagnostic_reports_running_health_as_unverified(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    pid_path = runtime_root / "sayane-resident.pid"
    lock_path = runtime_root / "sayane-resident.lock"
    pid_path.write_text("12345\n", encoding="utf-8")
    lock_path.write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr("sayane.app.daemon_process_control._is_pid_running", lambda pid: True)
    monkeypatch.setattr("sayane.app.daemon_process_control._healthcheck", lambda url, timeout=0.2: True)

    status_report = build_daemon_status_report(runtime_root)
    payload = build_readiness_diagnostic_from_status_report(status_report).public_metadata()

    assert payload["readiness_status"] == ResidentDaemonReadinessStatus.READINESS_UNVERIFIED.value
    assert (
        payload["api_readiness_status"]
        == ResidentDaemonApiReadinessStatus.API_READINESS_UNVERIFIED.value
    )
    assert payload["evidence_ceiling"] == "unauthenticated_health_endpoint_only"
    assert payload["manual_review_required"] is False
    assert payload["status_report"]["state"] == "running"
    assert payload["proves_process_identity"] is False
    assert payload["proves_daemon_readiness"] is False
    assert payload["proves_api_readiness"] is False
