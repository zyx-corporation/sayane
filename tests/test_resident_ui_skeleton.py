"""Tests for minimal resident UI review queue and MCP preview skeleton (#181)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.app.capabilities import CapabilityError, create_local_capability_token
from sayane.app.ui import build_mcp_preview, build_review_queue
from sayane.core.candidate import (
    CaptureMetadata,
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
)
from sayane.core.review_decision import ReviewDecision
from sayane.storage.repositories import build_test_repository_bundle


def _candidate(candidate_id: str, *, status: str = "pending") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status=status,  # type: ignore[arg-type]
        target_profile_id="default",
        content=f"content for {candidate_id}",
        display_summary=f"summary for {candidate_id}",
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
        ),
        source=CandidateSource(
            type="clipboard",
            captured_at=datetime.now(UTC),
        ),
        proposal=CandidateProposal(
            section="important_terms",
            add=[candidate_id],
            summary=f"summary for {candidate_id}",
        ),
    )


def test_review_queue_requires_ui_capability() -> None:
    repositories = build_test_repository_bundle(profile_id="default")
    capability = create_local_capability_token(["mcp"])

    with pytest.raises(CapabilityError, match="ui"):
        build_review_queue(repositories, capability=capability)


def test_review_queue_lists_pending_candidates_without_profile_write() -> None:
    repositories = build_test_repository_bundle(profile_id="default")
    repositories.candidates.save(_candidate("c-pending"))
    repositories.candidates.save(_candidate("c-approved", status="approved"))
    capability = create_local_capability_token(["ui"])

    queue = build_review_queue(repositories, capability=capability)

    assert queue["kind"] == "resident_review_queue"
    assert queue["is_review_surface"] is True
    assert queue["is_mcp_context"] is False
    assert [item["candidate_id"] for item in queue["items"]] == ["c-pending"]
    assert queue["items"][0]["capture_source"] == "clipboard"
    assert repositories.profile_context is not None
    assert repositories.profile_context.load_context("profile") is None


def test_mcp_preview_requires_mcp_capability() -> None:
    repositories = build_test_repository_bundle(profile_id="default")
    capability = create_local_capability_token(["ui"])

    with pytest.raises(CapabilityError, match="mcp"):
        build_mcp_preview(repositories, capability=capability)


def test_mcp_preview_marks_derived_context_and_blocks_pending_and_rejected() -> None:
    repositories = build_test_repository_bundle(profile_id="default")
    repositories.candidates.save(_candidate("c-approved"))
    repositories.candidates.save(_candidate("c-rejected"))
    repositories.candidates.save(_candidate("c-pending"))
    repositories.review_decisions.append(
        ReviewDecision(
            candidate_id="c-approved",
            decision="approve",
            reason="accepted",
            applied_value="approved value",
            original_section="important_terms",
        )
    )
    repositories.review_decisions.append(
        ReviewDecision(
            candidate_id="c-rejected",
            decision="reject",
            reason="not acceptable",
            applied_value="rejected value",
            original_section="important_terms",
        )
    )
    capability = create_local_capability_token(["mcp"])

    preview = build_mcp_preview(repositories, capability=capability)

    assert preview["preview"] == {
        "kind": "resident_mcp_preview",
        "is_preview": True,
        "is_derived_context": True,
        "is_canonical_profile": False,
    }
    assert preview["is_derived_context"] is True
    assert preview["is_canonical_profile"] is False
    assert [entry["candidate_id"] for entry in preview["included_approved_candidates"]] == [
        "c-approved"
    ]
    assert preview["included_approved_candidates"][0]["content"] == "approved value"
    blocked = {entry["candidate_id"]: entry for entry in preview["blocked_candidates"]}
    assert blocked["c-rejected"]["exposure_class"] == "rejected_candidate"
    assert blocked["c-pending"]["exposure_class"] == "pending_candidate"
    assert "rejected value" not in str(preview)
    assert "content for c-pending" not in str(preview)
