"""Tests for ADR 0007 Phase 2 review decision repository seam."""

from __future__ import annotations

from sayane.core.mcp_context import build_compiled_context
from sayane.core.review_decision import (
    ReviewDecision,
    clear_decisions,
    clear_review_decision_repository,
    get_decisions_for_candidate,
    get_review_decision_repository,
    list_decisions,
    load_review_decisions,
    save_decision,
    set_review_decision_repository,
)
from sayane.storage.repositories import TestOnlyInMemoryReviewDecisionRepository


def _decision(candidate_id: str = "candidate-repo") -> ReviewDecision:
    return ReviewDecision(
        candidate_id=candidate_id,
        decision="approve",
        reason="Accepted through repository seam.",
        applied_value="Repository-backed review context.",
        original_section="project.context",
        original_action="append",
    )


def test_review_decision_repository_seam_feeds_save_and_list() -> None:
    profile_id = "repo-seam-save-list"
    clear_decisions(profile_id)
    repository = TestOnlyInMemoryReviewDecisionRepository()
    set_review_decision_repository(profile_id, repository)

    decision = _decision()
    save_decision(profile_id, decision)

    assert get_review_decision_repository(profile_id) is repository
    assert list_decisions(profile_id) == [decision]
    assert load_review_decisions(profile_id) == [decision]
    assert get_decisions_for_candidate(decision.candidate_id, profile_id) == [decision]

    clear_decisions(profile_id)
    assert get_review_decision_repository(profile_id) is None


def test_review_decision_repository_seam_preserves_legacy_fallback() -> None:
    profile_id = "repo-seam-fallback"
    clear_decisions(profile_id)
    decision = _decision("candidate-fallback")

    save_decision(profile_id, decision)

    assert get_review_decision_repository(profile_id) is None
    assert list_decisions(profile_id) == [decision]
    assert load_review_decisions(profile_id) == [decision]

    clear_decisions(profile_id)


def test_repository_backed_review_decisions_feed_compiled_context() -> None:
    profile_id = "repo-seam-mcp"
    clear_decisions(profile_id)
    repository = TestOnlyInMemoryReviewDecisionRepository()
    set_review_decision_repository(profile_id, repository)
    decision = _decision("candidate-mcp-repo")

    save_decision(profile_id, decision)
    compiled = build_compiled_context(
        profile_id=profile_id,
        mode="full",
        scoped_decisions=load_review_decisions(profile_id),
    )

    assert compiled["included_approved_candidates"][0]["candidate_id"] == "candidate-mcp-repo"
    assert compiled["included_approved_candidates"][0]["content"] == (
        "Repository-backed review context."
    )

    clear_decisions(profile_id)


def test_clear_review_decision_repository_only_removes_repository_binding() -> None:
    profile_id = "repo-seam-clear-repo"
    clear_decisions(profile_id)
    repository = TestOnlyInMemoryReviewDecisionRepository()
    set_review_decision_repository(profile_id, repository)

    assert get_review_decision_repository(profile_id) is repository
    clear_review_decision_repository(profile_id)
    assert get_review_decision_repository(profile_id) is None
