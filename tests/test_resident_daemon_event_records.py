"""Tests for resident daemon event record schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonEventCategory,
    ResidentDaemonEventRecord,
    ResidentDaemonEventResult,
    ResidentDaemonPreflightCategory,
    ResidentDaemonPreflightItem,
    ResidentDaemonPreflightReport,
    ResidentDaemonPreflightStatus,
    build_cleanup_apply_event_record,
    build_repair_apply_event_record,
    build_readiness_event_record,
    build_runtime_init_plan,
    build_preflight_event_record,
    build_process_control_event_record,
    build_runtime_init_event_record,
)


def test_preview_event_record_public_metadata_is_non_persistent(tmp_path: Path) -> None:
    record = ResidentDaemonEventRecord(
        operation_id="preview-001",
        category=ResidentDaemonEventCategory.PREVIEW,
        surface="daemon-liveness-diagnostic",
        runtime_root=tmp_path / "run",
        evidence=("pid_missing_liveness_unverified",),
        message="preview only",
    )

    assert record.public_metadata() == {
        "kind": "resident_daemon_event_record",
        "operation_id": "preview-001",
        "category": "preview",
        "surface": "daemon-liveness-diagnostic",
        "result": "planned",
        "runtime_root": str(tmp_path / "run"),
        "evidence": ["pid_missing_liveness_unverified"],
        "consent": "not_required_for_preview",
        "message": "preview only",
        "mutates_filesystem": False,
        "controls_process": False,
        "exposes_ipc": False,
        "integrates_os_service": False,
        "persisted": False,
    }


def test_preview_event_record_rejects_side_effect_flags() -> None:
    with pytest.raises(ValueError, match="preview event records"):
        ResidentDaemonEventRecord(
            operation_id="preview-unsafe",
            category=ResidentDaemonEventCategory.PREVIEW,
            surface="daemon-runtime-layout",
            mutates_filesystem=True,
        )


def test_future_apply_event_can_record_required_flags_without_persistence(
    tmp_path: Path,
) -> None:
    record = ResidentDaemonEventRecord(
        operation_id="apply-001",
        category=ResidentDaemonEventCategory.APPLY,
        surface="future-daemon-runtime-init-apply",
        result=ResidentDaemonEventResult.REQUIRES_REVIEW,
        runtime_root=tmp_path / "run",
        evidence=("runtime_root_validated", "operator_confirmation_missing"),
        consent="required",
        message="schema only",
        mutates_filesystem=True,
    )

    payload = record.public_metadata()

    assert payload["category"] == "apply"
    assert payload["result"] == "requires_review"
    assert payload["mutates_filesystem"] is True
    assert payload["controls_process"] is False
    assert payload["exposes_ipc"] is False
    assert payload["integrates_os_service"] is False
    assert payload["persisted"] is False


def test_event_record_requires_operation_id_and_surface() -> None:
    with pytest.raises(ValueError, match="operation_id"):
        ResidentDaemonEventRecord(
            operation_id=" ",
            category=ResidentDaemonEventCategory.PREVIEW,
            surface="daemon-plan",
        )

    with pytest.raises(ValueError, match="surface"):
        ResidentDaemonEventRecord(
            operation_id="preview-002",
            category=ResidentDaemonEventCategory.PREVIEW,
            surface=" ",
        )


def test_future_process_ipc_and_service_flags_are_explicit() -> None:
    process_record = ResidentDaemonEventRecord(
        operation_id="process-001",
        category=ResidentDaemonEventCategory.PROCESS,
        surface="future-daemon-start",
        consent="required",
        controls_process=True,
    )
    ipc_record = ResidentDaemonEventRecord(
        operation_id="ipc-001",
        category=ResidentDaemonEventCategory.IPC,
        surface="future-daemon-local-ipc",
        exposes_ipc=True,
    )
    service_record = ResidentDaemonEventRecord(
        operation_id="service-001",
        category=ResidentDaemonEventCategory.SERVICE,
        surface="future-daemon-service-install",
        consent="required",
        integrates_os_service=True,
    )

    assert process_record.public_metadata()["controls_process"] is True
    assert ipc_record.public_metadata()["exposes_ipc"] is True
    assert service_record.public_metadata()["integrates_os_service"] is True
    assert process_record.public_metadata()["persisted"] is False
    assert ipc_record.public_metadata()["persisted"] is False
    assert service_record.public_metadata()["persisted"] is False


def test_build_preflight_event_record_maps_review_required_report() -> None:
    report = ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="ipc_authentication_future_work",
                category=ResidentDaemonPreflightCategory.IPC,
                status=ResidentDaemonPreflightStatus.REVIEW_REQUIRED,
                summary="future work",
            ),
            ResidentDaemonPreflightItem(
                key="audit_event_schema_available",
                category=ResidentDaemonPreflightCategory.RELEASE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="available",
            ),
        ),
    )

    record = build_preflight_event_record(report)
    payload = record.public_metadata()

    assert record.category is ResidentDaemonEventCategory.PREVIEW
    assert record.result is ResidentDaemonEventResult.REQUIRES_REVIEW
    assert payload["surface"] == "daemon-preflight"
    assert payload["evidence"] == ["ipc_authentication_future_work:review_required"]
    assert payload["mutates_filesystem"] is False
    assert payload["controls_process"] is False
    assert payload["exposes_ipc"] is False
    assert payload["integrates_os_service"] is False
    assert payload["persisted"] is False


def test_build_preflight_event_record_maps_blocked_report_to_failed() -> None:
    report = ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="process_control_blocked",
                category=ResidentDaemonPreflightCategory.PROCESS,
                status=ResidentDaemonPreflightStatus.BLOCKED,
                summary="blocked",
            ),
        ),
    )

    record = build_preflight_event_record(report, operation_id="preflight-001")

    assert record.operation_id == "preflight-001"
    assert record.result is ResidentDaemonEventResult.FAILED


def test_build_preflight_event_record_uses_all_keys_when_report_is_pass() -> None:
    report = ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="evidence_ladder_documented",
                category=ResidentDaemonPreflightCategory.EVIDENCE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="documented",
            ),
            ResidentDaemonPreflightItem(
                key="mutation_boundary_documented",
                category=ResidentDaemonPreflightCategory.MUTATION,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="documented",
            ),
        ),
    )

    payload = build_preflight_event_record(report).public_metadata()

    assert payload["result"] == "succeeded"
    assert payload["evidence"] == [
        "evidence_ladder_documented",
        "mutation_boundary_documented",
    ]


def test_build_runtime_init_event_record_for_preview(tmp_path: Path) -> None:
    plan = build_runtime_init_plan(tmp_path / "run", operation_id="init-preview-1")

    payload = build_runtime_init_event_record(
        plan,
        write_metadata=False,
        plan_fingerprint=plan.plan_fingerprint(),
        confirmation_matched=False,
        fingerprint_matched=False,
    ).public_metadata()

    assert payload["operation_id"] == "init-preview-1"
    assert payload["category"] == "preview"
    assert payload["surface"] == "daemon-runtime-init"
    assert payload["result"] == "planned"
    assert payload["mutates_filesystem"] is False
    assert payload["consent"] == "operator_apply_required"
    assert f"plan_fingerprint:{plan.plan_fingerprint()}" in payload["evidence"]
    assert "write_metadata_requested:false" in payload["evidence"]


def test_build_runtime_init_event_record_for_apply(tmp_path: Path) -> None:
    plan = build_runtime_init_plan(tmp_path / "run", operation_id="init-apply-1")

    payload = build_runtime_init_event_record(
        plan,
        applied=True,
        created_paths=(str(tmp_path / "run"),),
        write_metadata=True,
        confirm_operation_id="init-apply-1",
        plan_fingerprint=plan.plan_fingerprint(),
        confirm_plan_fingerprint=plan.plan_fingerprint(),
        confirmation_matched=True,
        fingerprint_matched=True,
    ).public_metadata()

    assert payload["operation_id"] == "init-apply-1"
    assert payload["category"] == "apply"
    assert payload["result"] == "succeeded"
    assert payload["mutates_filesystem"] is True
    assert payload["consent"] == "operator_apply_and_confirm_required"
    assert "write_metadata_requested:true" in payload["evidence"]
    assert "confirm_operation_id:init-apply-1" in payload["evidence"]
    assert f"plan_fingerprint:{plan.plan_fingerprint()}" in payload["evidence"]
    assert f"confirm_plan_fingerprint:{plan.plan_fingerprint()}" in payload["evidence"]
    assert "confirmation_matched:true" in payload["evidence"]
    assert "fingerprint_matched:true" in payload["evidence"]


def test_build_cleanup_apply_event_record_for_apply(tmp_path: Path) -> None:
    payload = build_cleanup_apply_event_record(
        operation_id="cleanup-apply-1",
        runtime_root=tmp_path / "run",
        requested_targets=("pid_file",),
        removed_paths=(str(tmp_path / "run" / "sayane-resident.pid"),),
        result="applied",
        applied=True,
    ).public_metadata()

    assert payload["surface"] == "daemon-cleanup-apply"
    assert payload["category"] == "apply"
    assert payload["result"] == "succeeded"
    assert payload["mutates_filesystem"] is True


def test_build_repair_apply_event_record_for_apply(tmp_path: Path) -> None:
    payload = build_repair_apply_event_record(
        operation_id="repair-apply-1",
        runtime_root=tmp_path / "run",
        requested_targets=("log_dir",),
        created_paths=(str(tmp_path / "run" / "logs"),),
        result="applied",
        applied=True,
    ).public_metadata()

    assert payload["surface"] == "daemon-repair-apply"
    assert payload["category"] == "apply"
    assert payload["result"] == "succeeded"
    assert payload["mutates_filesystem"] is True


def test_build_readiness_event_record_for_preview(tmp_path: Path) -> None:
    payload = build_readiness_event_record(
        operation_id="readiness-preview-1",
        runtime_root=tmp_path / "run",
        operation_class="diagnostics",
        readiness_status="readiness_unverified",
        api_readiness_status="api_readiness_unverified",
        evidence_ceiling="unauthenticated_health_endpoint_only",
        manual_review_required=False,
    ).public_metadata()

    assert payload["surface"] == "daemon-readiness-diagnostic"
    assert payload["category"] == "preview"
    assert payload["result"] == "planned"
    assert payload["mutates_filesystem"] is False


def test_build_process_control_event_record_for_started_daemon(tmp_path: Path) -> None:
    payload = build_process_control_event_record(
        operation_id="daemon-start-001",
        operation="start",
        runtime_root=tmp_path / "run",
        result="started",
        state_before="stopped",
        state_after="running",
        host="127.0.0.1",
        port=38741,
        pid=43210,
        applied=True,
    ).public_metadata()

    assert payload["category"] == "process"
    assert payload["surface"] == "daemon-start"
    assert payload["result"] == "succeeded"
    assert payload["controls_process"] is True
    assert payload["exposes_ipc"] is True
    assert "operation:start" in payload["evidence"]
    assert "pid:43210" in payload["evidence"]


def test_build_process_control_event_record_for_manual_review(tmp_path: Path) -> None:
    payload = build_process_control_event_record(
        operation_id="daemon-stop-001",
        operation="stop",
        runtime_root=tmp_path / "run",
        result="requires_review",
        state_before="failed",
        state_after="failed",
        host="127.0.0.1",
        port=38741,
        failure_mode="stale_pid_file",
        manual_review_required=True,
        applied=False,
    ).public_metadata()

    assert payload["category"] == "process"
    assert payload["surface"] == "daemon-stop"
    assert payload["result"] == "requires_review"
    assert payload["controls_process"] is True
    assert "failure_mode:stale_pid_file" in payload["evidence"]


def test_build_cleanup_apply_event_record_for_success(tmp_path: Path) -> None:
    payload = build_cleanup_apply_event_record(
        operation_id="daemon-cleanup-001",
        runtime_root=tmp_path / "run",
        requested_targets=("pid_file",),
        removed_paths=(str(tmp_path / "run" / "sayane-resident.pid"),),
        result="applied",
        applied=True,
    ).public_metadata()

    assert payload["category"] == "apply"
    assert payload["surface"] == "daemon-cleanup-apply"
    assert payload["result"] == "succeeded"
    assert payload["mutates_filesystem"] is True
    assert "requested_target:pid_file" in payload["evidence"]
