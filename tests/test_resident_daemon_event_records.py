"""Tests for resident daemon event record schema."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.app import (
    ResidentDaemonEventCategory,
    ResidentDaemonEventRecord,
    ResidentDaemonEventResult,
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
