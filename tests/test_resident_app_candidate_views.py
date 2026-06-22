"""Tests for app-facing candidate view-model helpers."""

from sayane.app import (
    build_app_candidate_detail,
    build_app_candidate_diff,
    build_app_candidate_queue,
)


def test_build_app_candidate_queue_adds_status_counts_and_sections() -> None:
    payload = build_app_candidate_queue(
        [
            {"id": "c1", "status": "pending", "section": "knowledge.concepts"},
            {"id": "c2", "status": "evaluated", "section": "knowledge.concepts"},
            {"id": "c3", "status": "pending", "section": "important_terms"},
        ]
    )

    assert payload["kind"] == "resident_app_candidate_queue"
    assert payload["reviewable_count"] == 3
    assert payload["status_counts"] == {"pending": 2, "evaluated": 1}
    assert payload["top_sections"][0] == {"section": "knowledge.concepts", "count": 2}


def test_build_app_candidate_detail_adds_ui_summary_and_allowed_actions() -> None:
    payload = build_app_candidate_detail(
        {
            "id": "c1",
            "status": "evaluated",
            "proposal": {"section": "knowledge.concepts", "operation": "add"},
            "source": {"type": "clipboard"},
            "evaluation": {"level": 1, "rde_class": "Preserved"},
        }
    )

    assert payload["ui_summary"]["section"] == "knowledge.concepts"
    assert payload["ui_summary"]["can_approve"] is True
    assert payload["allowed_actions"]["approve"] is True
    assert payload["allowed_actions"]["revise"] is True


def test_build_app_candidate_diff_adds_ui_summary() -> None:
    payload = build_app_candidate_diff(
        {
            "section": "important_terms",
            "recommended_section": "important_terms",
            "profile_update_recommended": True,
            "has_duplicates": False,
            "add": [{"name": "Context-Aware Harness"}],
            "already_present": [{"name": "Sayane"}],
            "remove": [],
            "list_diff": {
                "operation": "list_add",
                "added": ["Context-Aware Harness"],
                "removed": [],
                "unchanged_count": 1,
            },
        }
    )

    assert payload["ui_summary"]["section"] == "important_terms"
    assert payload["ui_summary"]["added_count"] == 1
    assert payload["ui_summary"]["already_present_count"] == 1
    assert payload["ui_summary"]["list_operation"] == "list_add"
    assert payload["ui_summary"]["has_structured_list_diff"] is True
