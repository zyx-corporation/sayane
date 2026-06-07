"""T-RDE tests for MCP Scoped Context Output (F-2)."""
from sayane.core.review_decision import ReviewDecision, save_decision
from sayane.core.mcp_context import build_compiled_context, render_compiled_context_text


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
