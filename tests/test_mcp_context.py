"""T-RDE tests for MCP Scoped Context Output (F-2)."""
from sayane.core.review_decision import ReviewDecision, save_decision
from sayane.core.mcp_context import (
    build_compiled_context,
    build_mcp_exposure_denial,
    can_expose_candidate_content_via_mcp,
    filter_mcp_exposable_candidates,
    get_candidate_mcp_exposure_class,
    render_compiled_context_text,
)


def _make_scoped_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-scoped-mcp",
        decision="scoped_accept",
        reason="Locally useful but not global.",
        accepted_scope={"level": "project", "target": "zenn", "sub_scope": "intro"},
        conditions=["問題意識を喚起する目的に限定"],
        negative_constraints=["global writing preference に昇格しない"],
        promotion_policy={"can_promote": False},
        reuse_policy={"review_on_reuse": True},
    )


def _make_approved_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-approved-mcp",
        decision="approve",
        reason="Accepted after human review.",
        applied_value="Use Candidate review boundary for MCP reuse.",
        original_section="project.context",
        original_action="append",
        original_proposed="Use Candidate review boundary for MCP reuse.",
    )


def _make_rejected_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-rejected-mcp",
        decision="reject",
        reason="Too broad for profile context.",
        applied_value="MUST NOT LEAK",
        original_section="profile.rules",
        original_action="append",
        original_proposed="MUST NOT LEAK",
    )


def _make_deferred_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-deferred-mcp",
        decision="defer",
        reason="Needs more review.",
        applied_value="MUST NOT LEAK EITHER",
        original_section="project.context",
        original_action="append",
        original_proposed="MUST NOT LEAK EITHER",
    )


def test_mcp_output_is_derived_context_not_canonical():
    compiled = build_compiled_context(target="cursor", mode="full")
    assert compiled["is_derived_context"] is True
    assert compiled["is_canonical_profile"] is False


def test_mcp_output_preserves_scoped_accept_metadata_in_full_mode():
    d = _make_scoped_decision()
    compiled = build_compiled_context(mode="full", scoped_decisions=[d])
    ctx = compiled["included_scoped_contexts"][0]
    assert ctx["accepted_scope"]["target"] == "zenn"
    assert "conditions" in ctx
    assert "negative_constraints" in ctx
    assert "昇格しない" in ctx["negative_constraints"][0]


def test_mcp_compact_mode_keeps_minimal_scope_note():
    d = _make_scoped_decision()
    compiled = build_compiled_context(mode="compact", scoped_decisions=[d])
    ctx = compiled["included_scoped_contexts"][0]
    assert "conditions_summary" in ctx or "key_constraint" in ctx


def test_mcp_strict_mode_omits_scoped_context():
    d = _make_scoped_decision()
    compiled = build_compiled_context(mode="strict", scoped_decisions=[d])
    assert len(compiled["included_scoped_contexts"]) == 0


def test_mcp_output_includes_boundary_warning():
    compiled = build_compiled_context(mode="full")
    assert len(compiled["warnings"]) >= 1
    assert "derived" in compiled["warnings"][0].lower() or "not the canonical" in compiled["warnings"][0].lower()


def test_render_compiled_context_text_shows_scope():
    d = _make_scoped_decision()
    compiled = build_compiled_context(mode="full", scoped_decisions=[d])
    text = render_compiled_context_text(compiled)
    assert "zenn" in text
    assert "昇格しない" in text


def test_promotion_not_allowed_in_mcp():
    d = _make_scoped_decision()
    compiled = build_compiled_context(mode="full", scoped_decisions=[d])
    ctx = compiled["included_scoped_contexts"][0]
    policy = ctx.get("promotion_policy", {})
    assert policy.get("can_promote") is False


def test_mcp_exposure_class_treats_missing_decision_as_pending():
    assert get_candidate_mcp_exposure_class(None) == "pending_candidate"
    assert can_expose_candidate_content_via_mcp(None) is False


def test_mcp_exposure_guard_allows_approved_candidate():
    decision = _make_approved_decision()
    assert get_candidate_mcp_exposure_class(decision) == "approved_candidate"
    assert can_expose_candidate_content_via_mcp(decision) is True


def test_mcp_exposure_guard_allows_scoped_accept_candidate():
    decision = _make_scoped_decision()
    assert get_candidate_mcp_exposure_class(decision) == "approved_candidate"
    assert can_expose_candidate_content_via_mcp(decision) is True


def test_mcp_exposure_guard_blocks_rejected_candidate_content():
    decision = _make_rejected_decision()
    assert get_candidate_mcp_exposure_class(decision) == "rejected_candidate"
    assert can_expose_candidate_content_via_mcp(decision) is False


def test_mcp_exposure_guard_blocks_deferred_candidate_content():
    decision = _make_deferred_decision()
    assert get_candidate_mcp_exposure_class(decision) == "pending_candidate"
    assert can_expose_candidate_content_via_mcp(decision) is False


def test_filter_mcp_exposable_candidates_blocks_unaccepted_content():
    approved = _make_approved_decision()
    rejected = _make_rejected_decision()
    deferred = _make_deferred_decision()
    exposable, denials = filter_mcp_exposable_candidates([approved, rejected, deferred, None])
    assert [d.candidate_id for d in exposable] == ["c-approved-mcp"]
    assert len(denials) == 3
    assert all(d["exposes_content"] is False for d in denials)


def test_compiled_context_includes_approved_candidate_with_metadata():
    approved = _make_approved_decision()
    compiled = build_compiled_context(mode="full", scoped_decisions=[approved])
    ctx = compiled["included_approved_candidates"][0]
    assert ctx["candidate_id"] == "c-approved-mcp"
    assert ctx["section"] == "project.context"
    assert ctx["lineage_event_id"] == approved.lineage_event_id
    assert ctx["content"] == "Use Candidate review boundary for MCP reuse."


def test_compiled_context_blocks_rejected_candidate_content():
    rejected = _make_rejected_decision()
    compiled = build_compiled_context(mode="full", scoped_decisions=[rejected])
    assert compiled["included_approved_candidates"] == []
    assert compiled["included_scoped_contexts"] == []
    assert compiled["blocked_candidates"][0]["candidate_id"] == "c-rejected-mcp"
    assert compiled["blocked_candidates"][0]["exposes_content"] is False
    rendered = render_compiled_context_text(compiled)
    assert "MUST NOT LEAK" not in rendered


def test_build_mcp_exposure_denial_is_narrow_and_fail_closed():
    denial = build_mcp_exposure_denial(
        "candidate_not_approved",
        candidate_id="c-pending-mcp",
        exposure_class="pending_candidate",
    )
    assert denial["ok"] is False
    assert denial["candidate_id"] == "c-pending-mcp"
    assert denial["exposes_content"] is False
    assert "content" not in denial


# ---------- MCP entrypoint smoke tests ----------


def test_compiled_context_mcp_tool_returns_derived_context():
    """compiled_context tool returns is_derived_context=True."""
    from sayane.mcp.operations import get_operations

    ops = get_operations()
    result = ops.build_compiled_context(target="cursor", mode="compact")
    assert result["is_derived_context"] is True
    assert result["is_canonical_profile"] is False
    assert result["target"] == "cursor"


def test_compiled_context_mcp_tool_blocks_pending_content():
    """compiled_context tool blocks pending candidate content."""
    from sayane.core.review_decision import ReviewDecision
    from sayane.core.mcp_context import build_compiled_context

    pending = ReviewDecision(
        candidate_id="c-pending-test",
        decision="defer",
        reason="Needs review.",
        applied_value="PENDING CONTENT MUST NOT LEAK",
    )
    compiled = build_compiled_context(
        mode="full",
        scoped_decisions=[pending],
    )
    assert compiled["included_approved_candidates"] == []
    assert compiled["included_scoped_contexts"] == []
    assert len(compiled["blocked_candidates"]) >= 1
    assert compiled["blocked_candidates"][0]["candidate_id"] == "c-pending-test"
    assert compiled["blocked_candidates"][0]["exposes_content"] is False


def test_compiled_context_mcp_tool_blocks_rejected_content():
    """compiled_context tool blocks rejected candidate content."""
    from sayane.core.review_decision import ReviewDecision
    from sayane.core.mcp_context import build_compiled_context

    rejected = ReviewDecision(
        candidate_id="c-rejected-test",
        decision="reject",
        reason="Too broad.",
        applied_value="REJECTED CONTENT MUST NOT LEAK",
    )
    compiled = build_compiled_context(
        mode="full",
        scoped_decisions=[rejected],
    )
    assert compiled["included_approved_candidates"] == []
    assert compiled["included_scoped_contexts"] == []
    assert len(compiled["blocked_candidates"]) >= 1
    assert compiled["blocked_candidates"][0]["exposes_content"] is False


def test_compiled_context_mcp_tool_allows_approved_content():
    """compiled_context tool allows approved candidate content."""
    from sayane.core.review_decision import ReviewDecision
    from sayane.core.mcp_context import build_compiled_context

    approved = ReviewDecision(
        candidate_id="c-approved-test",
        decision="approve",
        reason="Accepted.",
        applied_value="Safe content for editor context.",
        original_section="project.context",
    )
    compiled = build_compiled_context(
        mode="full",
        scoped_decisions=[approved],
    )
    assert len(compiled["included_approved_candidates"]) == 1
    assert compiled["included_approved_candidates"][0]["candidate_id"] == "c-approved-test"
    assert compiled["included_approved_candidates"][0]["content"] == "Safe content for editor context."
    assert len(compiled["blocked_candidates"]) == 0


def test_compiled_context_mcp_tool_includes_scoped_accept_metadata():
    """compiled_context tool includes scope/conditions/constraints for scoped_accept."""
    from sayane.core.review_decision import ReviewDecision
    from sayane.core.mcp_context import build_compiled_context

    scoped = ReviewDecision(
        candidate_id="c-scoped-test",
        decision="scoped_accept",
        reason="Locally useful.",
        accepted_scope={"level": "project", "target": "sayane", "sub_scope": "mcp"},
        conditions=["Use only for MCP integration docs."],
        negative_constraints=["Do not treat as global writing style."],
        promotion_policy={"can_promote": False},
        reuse_policy={"review_on_reuse": True},
    )
    compiled = build_compiled_context(
        mode="full",
        scoped_decisions=[scoped],
    )
    assert len(compiled["included_scoped_contexts"]) == 1
    ctx = compiled["included_scoped_contexts"][0]
    assert ctx["accepted_scope"]["target"] == "sayane"
    assert "conditions" in ctx
    assert "negative_constraints" in ctx
    assert ctx["promotion_policy"]["can_promote"] is False
    assert ctx["reuse_policy"]["review_on_reuse"] is True
    # Also in approved list
    assert len(compiled["included_approved_candidates"]) == 1


def test_compiled_context_empty_decisions_fail_safe():
    """compiled_context with no decisions returns empty output, not crash."""
    from sayane.core.mcp_context import build_compiled_context

    compiled = build_compiled_context(target="cursor", mode="compact")
    assert compiled["included_approved_candidates"] == []
    assert compiled["included_scoped_contexts"] == []
    assert compiled["is_derived_context"] is True


def test_compiled_context_blocks_deferred_candidate():
    """compiled_context blocks deferred (pending) candidate content."""
    from sayane.core.review_decision import ReviewDecision
    from sayane.core.mcp_context import build_compiled_context

    deferred = ReviewDecision(
        candidate_id="c-deferred-test",
        decision="defer",
        reason="Needs more review.",
        applied_value="DEFERRED CONTENT MUST NOT LEAK",
    )
    compiled = build_compiled_context(
        mode="full",
        scoped_decisions=[deferred],
    )
    assert compiled["included_approved_candidates"] == []
    assert len(compiled["blocked_candidates"]) >= 1
    assert compiled["blocked_candidates"][0]["exposes_content"] is False
