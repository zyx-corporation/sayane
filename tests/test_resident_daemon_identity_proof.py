"""Tests for resident daemon identity-proof preview."""

from __future__ import annotations

from pathlib import Path

from sayane.app import (
    ResidentDaemonIdentityProofStatus,
    build_daemon_status_report,
    build_identity_proof,
    build_identity_proof_from_status_report,
    build_runtime_init_plan,
)
from sayane.app.daemon_runtime_init import apply_runtime_init


def test_identity_proof_reports_stopped_daemon_as_not_running(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"

    payload = build_identity_proof(runtime_root).public_metadata()

    assert payload["kind"] == "resident_daemon_identity_proof_preview"
    assert payload["preview_only"] is True
    assert payload["identity_status"] == ResidentDaemonIdentityProofStatus.IDENTITY_NOT_RUNNING.value
    assert payload["downgrade_reason"] == "no_running_process"
    assert payload["evidence_ceiling"] == "no_running_process"
    assert payload["manual_review_required"] is False
    assert payload["proves_process_identity"] is False
    assert payload["proves_daemon_readiness"] is False
    assert payload["proves_api_readiness"] is False


def test_identity_proof_reports_manual_review_when_status_is_ambiguous(
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    (runtime_root / "sayane-resident.pid").write_text("12345\n", encoding="utf-8")

    payload = build_identity_proof(runtime_root).public_metadata()

    assert payload["identity_status"] == ResidentDaemonIdentityProofStatus.MANUAL_REVIEW_REQUIRED.value
    assert payload["downgrade_reason"] == "process_status_requires_manual_review"
    assert payload["manual_review_required"] is True
    assert payload["evidence_ceiling"] == "process_status_requires_manual_review"


def test_identity_proof_reports_running_health_as_unverified(
    tmp_path: Path,
    monkeypatch,
) -> None:
    runtime_root = tmp_path / "run"
    apply_runtime_init(build_runtime_init_plan(runtime_root))
    (runtime_root / "sayane-resident.pid").write_text("12345\n", encoding="utf-8")
    (runtime_root / "sayane-resident.lock").write_text("{}\n", encoding="utf-8")
    monkeypatch.setattr("sayane.app.daemon_process_control._is_pid_running", lambda pid: True)
    monkeypatch.setattr("sayane.app.daemon_process_control._healthcheck", lambda url, timeout=0.2: True)

    status_report = build_daemon_status_report(runtime_root)
    payload = build_identity_proof_from_status_report(status_report).public_metadata()

    assert payload["identity_status"] == ResidentDaemonIdentityProofStatus.IDENTITY_UNVERIFIED.value
    assert payload["downgrade_reason"] == "unauthenticated_health_endpoint_only"
    assert payload["evidence_ceiling"] == "unauthenticated_health_endpoint_only"
    assert payload["manual_review_required"] is False
    assert payload["status_report"]["state"] == "running"
    assert payload["identity"]["runtime_dir"] == str(runtime_root)
