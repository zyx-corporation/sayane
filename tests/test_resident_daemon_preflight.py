"""Tests for resident daemon preflight checklist model."""

from __future__ import annotations

import json

import pytest

from sayane.app import (
    ResidentDaemonPreflightCategory,
    ResidentDaemonPreflightItem,
    ResidentDaemonPreflightReport,
    ResidentDaemonPreflightStatus,
    build_implementation_gate_preflight_report,
)


def test_default_implementation_gate_preflight_report_is_json_friendly() -> None:
    payload = build_implementation_gate_preflight_report().public_metadata()

    assert payload["kind"] == "resident_daemon_preflight_report"
    assert payload["target_scope"] == "resident_daemon_implementation_gate"
    assert payload["status"] == "review_required"
    assert payload["mutates_filesystem"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["exposes_ipc"] is False
    assert payload["integrates_os_service"] is False
    assert {item["key"] for item in payload["items"]} == {
        "evidence_ladder_documented",
        "mutation_boundary_documented",
        "operator_consent_documented",
        "ipc_authentication_future_work",
        "process_control_future_work",
        "os_service_integration_deferred",
        "audit_event_schema_available",
    }
    json.dumps(payload)


def test_preflight_report_aggregate_status_prefers_blocked() -> None:
    report = ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="ok",
                category=ResidentDaemonPreflightCategory.EVIDENCE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="ok",
            ),
            ResidentDaemonPreflightItem(
                key="blocked",
                category=ResidentDaemonPreflightCategory.PROCESS,
                status=ResidentDaemonPreflightStatus.BLOCKED,
                summary="blocked",
            ),
        ),
    )

    assert report.status is ResidentDaemonPreflightStatus.BLOCKED
    assert report.public_metadata()["status"] == "blocked"


def test_preflight_report_aggregate_status_prefers_review_before_pass() -> None:
    report = ResidentDaemonPreflightReport(
        items=(
            ResidentDaemonPreflightItem(
                key="ok",
                category=ResidentDaemonPreflightCategory.EVIDENCE,
                status=ResidentDaemonPreflightStatus.PASS,
                summary="ok",
            ),
            ResidentDaemonPreflightItem(
                key="review",
                category=ResidentDaemonPreflightCategory.IPC,
                status=ResidentDaemonPreflightStatus.REVIEW_REQUIRED,
                summary="review",
            ),
        ),
    )

    assert report.status is ResidentDaemonPreflightStatus.REVIEW_REQUIRED


def test_preflight_item_requires_key_and_summary() -> None:
    with pytest.raises(ValueError, match="key"):
        ResidentDaemonPreflightItem(
            key=" ",
            category=ResidentDaemonPreflightCategory.RELEASE,
            status=ResidentDaemonPreflightStatus.PASS,
            summary="ok",
        )

    with pytest.raises(ValueError, match="summary"):
        ResidentDaemonPreflightItem(
            key="ok",
            category=ResidentDaemonPreflightCategory.RELEASE,
            status=ResidentDaemonPreflightStatus.PASS,
            summary=" ",
        )
