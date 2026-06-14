"""Tests for persistent ReviewDecision local working store."""

from __future__ import annotations

from pathlib import Path

import pytest

from sayane.bridge.config import BridgeConfig
from sayane.core.review_decision import ReviewDecision
from sayane.mcp.operations import McpOperations
from sayane.storage.review_decisions import (
    append_review_decision,
    list_review_decisions,
    review_decisions_path,
)
from sayane.storage.security_policy import StorageSecurityError


def test_append_and_list_review_decisions(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane-home")
    decision = ReviewDecision(
        candidate_id="c-approved",
        decision="approve",
        reason="Approved after review.",
        applied_value="approved context",
        original_section="knowledge.concepts",
        original_action="add",
        original_proposed="approved context",
    )

    path = append_review_decision(config, "default", decision)
    assert path == review_decisions_path(config, "default")
    loaded = list_review_decisions(config, "default")
    assert len(loaded) == 1
    assert loaded[0].candidate_id == "c-approved"
    assert loaded[0].decision == "approve"
    assert loaded[0].applied_value == "approved context"


def test_review_decision_write_blocks_git_home(tmp_path: Path) -> None:
    home = tmp_path / "repo-home"
    home.mkdir()
    (home / ".git").mkdir()
    config = BridgeConfig(home=home)
    decision = ReviewDecision(candidate_id="c1", decision="approve", reason="ok")

    with pytest.raises(StorageSecurityError) as exc:
        append_review_decision(config, "default", decision)
    assert exc.value.decision.reason == "git_worktree_on_hold"


def test_mcp_compiled_context_uses_persisted_review_decisions(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane-home")
    append_review_decision(
        config,
        "default",
        ReviewDecision(
            candidate_id="c-approved",
            decision="approve",
            reason="Approved after review.",
            applied_value="approved context for cursor",
            original_section="knowledge.concepts",
            original_action="add",
            original_proposed="approved context for cursor",
        ),
    )
    append_review_decision(
        config,
        "default",
        ReviewDecision(
            candidate_id="c-rejected",
            decision="reject",
            reason="Rejected after review.",
            original_section="knowledge.concepts",
            original_action="add",
            original_proposed="MUST NOT APPEAR",
        ),
    )

    compiled = McpOperations(config).build_compiled_context(
        target="cursor",
        profile_id="default",
        mode="full",
    )

    approved = compiled["included_approved_candidates"]
    assert len(approved) == 1
    assert approved[0]["candidate_id"] == "c-approved"
    assert approved[0]["content"] == "approved context for cursor"
    assert compiled["blocked_candidates"][0]["candidate_id"] == "c-rejected"
    assert "MUST NOT APPEAR" not in str(compiled)
