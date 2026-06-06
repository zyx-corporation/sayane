"""T-RDE tests for Scoped Context Acceptance (F-1.5)."""
from sayane.core.review_decision import (
    ReviewDecision,
    build_lineage_event,
    save_decision,
    validate_decision,
)


def test_scoped_accept_records_scope_and_conditions():
    d = ReviewDecision(
        candidate_id="c-1",
        decision="scoped_accept",
        reason="Locally useful but not global policy.",
        accepted_scope={"level": "project", "target": "zenn", "sub_scope": "intro"},
        conditions=["読者の問題意識を喚起する目的に限定"],
        negative_constraints=["global writing preference に昇格しない"],
        promotion_policy={"can_promote": False},
        reuse_policy={"review_on_reuse": True},
    )
    save_decision("test-scoped", d)
    lineage = build_lineage_event(d)
    assert lineage["decision"]["type"] == "scoped_accept"
    sa = lineage["scoped_accept"]
    assert sa["accepted_scope"]["level"] == "project"
    assert "読者の問題意識" in sa["conditions"][0]
    assert "昇格しない" in sa["negative_constraints"][0]
    assert sa["promotion_policy"]["can_promote"] is False


def test_scoped_accept_requires_reason():
    d = ReviewDecision(candidate_id="c-2", decision="scoped_accept", reason="")
    errors = validate_decision(d, has_review_required=False)
    assert any("reason" in e.lower() for e in errors)


def test_scoped_accept_requires_scope():
    d = ReviewDecision(candidate_id="c-3", decision="scoped_accept", reason="ok")
    errors = validate_decision(d, has_review_required=False)
    assert any("scope" in e.lower() for e in errors)


def test_negative_constraints_preserved_in_audit():
    d = ReviewDecision(
        candidate_id="c-4",
        decision="scoped_accept",
        reason="Conditional.",
        accepted_scope={"level": "project"},
        negative_constraints=["Do not promote to global", "Keep scope on MCP output"],
    )
    save_decision("test-scoped", d)
    lineage = build_lineage_event(d)
    assert "Do not promote to global" in lineage["scoped_accept"]["negative_constraints"]


def test_promotion_guard_blocks_project_to_global_without_review():
    d = ReviewDecision(
        candidate_id="c-5",
        decision="scoped_accept",
        reason="Conditional.",
        accepted_scope={"level": "project"},
        promotion_policy={"can_promote": False, "requires_review_for": ["project_to_global"]},
    )
    lineage = build_lineage_event(d)
    assert lineage["scoped_accept"]["promotion_policy"]["can_promote"] is False


def test_approve_still_works():
    d = ReviewDecision(candidate_id="c-6", decision="approve", reason="ok")
    save_decision("test-scoped", d)
    errors = validate_decision(d, has_review_required=False)
    assert errors == []


def test_scoped_accept_lineage_has_all_metadata():
    d = ReviewDecision(
        candidate_id="c-7",
        decision="scoped_accept",
        reason="Scoped and conditional.",
        accepted_scope={"level": "project", "target": "test"},
        conditions=["condition 1"],
        negative_constraints=["constraint 1"],
        promotion_policy={"can_promote": False},
        reuse_policy={"review_on_reuse": True},
        review_flags=["partial_context_overgeneralization", "trojan_context_risk"],
    )
    lineage = build_lineage_event(d)
    assert "scoped_accept" in lineage
    assert "partial_context_overgeneralization" in lineage["semantic_review"]["flags"]
    assert "trojan_context_risk" in lineage["semantic_review"]["flags"]
