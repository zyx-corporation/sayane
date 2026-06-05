"""T-RDE tests for Provenance-aware Candidate Review UI (Phase 12)."""
from pathlib import Path

import yaml

from sayane.core.review_decision import (
    ReviewDecision,
    build_lineage_event,
    save_decision,
)
from sayane.core.import_policy import evaluate_policy


def _load_ui_fixture():
    path = Path(__file__).resolve().parent / "fixtures" / "ui" / "a2b-candidate-review-ui.yml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_a2b_ui_fixture_renders_review_context():
    fx = _load_ui_fixture()
    assert len(fx["candidates"]) == 2
    assert len(fx["overlap_groups"]) == 1
    og = fx["overlap_groups"][0]
    assert "rde" in og["terms"]
    assert "sayane" in og["terms"]


def test_candidate_card_shows_flags_and_warnings():
    decision = ReviewDecision(
        candidate_id="c-001",
        decision="approve",
        review_flags=["review_required", "unstable_placement", "semantic_overlap"],
        review_warnings=[{"type": "unstable_placement", "term": "RDE", "message": "RDE may be flattened."}],
        transfer_path=["Sayane", "ChatGPT", "Claude", "Sayane"],
    )
    save_decision("ui-test", decision)
    lineage = build_lineage_event(decision)
    assert "review_required" in lineage["semantic_review"]["flags"]
    assert "transfer_path" in lineage
    assert len(lineage["transfer_path"]) == 4


def test_policy_block_should_not_allow_import():
    result = evaluate_policy("strict", verification_status="unverified", semantic_flags=["semantic_overlap"])
    assert result.import_allowed is False
    assert result.status == "BLOCK"
    # Even when blocked, human review is still allowed
    assert result.review_allowed is True


def test_review_required_requires_reason():
    from sayane.core.review_decision import validate_decision
    d = ReviewDecision(candidate_id="c-001", decision="approve", reason="")
    errors = validate_decision(d, has_review_required=True)
    assert len(errors) >= 1


def test_modify_preserves_original_candidate():
    d = ReviewDecision(
        candidate_id="c-002",
        decision="modify",
        reason="Canonical wording.",
        applied_value={"principles": ["RDE", "Context portability via Sayane"]},
        original_section="principles",
        original_proposed={"principles": ["RDE", "Sayane"]},
    )
    save_decision("ui-test", d)
    lineage = build_lineage_event(d)
    assert lineage["candidate"]["proposed"] == {"principles": ["RDE", "Sayane"]}
    assert lineage["decision"]["applied_value"] == {"principles": ["RDE", "Context portability via Sayane"]}


def test_overlap_group_shows_terms():
    from sayane.core.review_decision import OverlapResolution, record_overlap_resolution, get_overlap_resolution
    res = OverlapResolution(
        overlap_id="overlap-001",
        terms=["rde", "sayane"],
        candidate_ids=["c-001", "c-002"],
        resolved=False,
    )
    record_overlap_resolution(res)
    retrieved = get_overlap_resolution("overlap-001")
    assert retrieved is not None
    assert retrieved.terms == ["rde", "sayane"]
    assert len(retrieved.candidate_ids) == 2


def test_missing_provenance_should_show_unknown():
    decision = ReviewDecision(
        candidate_id="c-003",
        decision="approve",
        transfer_path=[],  # no transfer path
    )
    lineage = build_lineage_event(decision)
    # Empty transfer path is preserved, not invented
    assert lineage["transfer_path"] == []


def test_rejected_candidates_visible():
    decision = ReviewDecision(candidate_id="c-rej", decision="reject", reason="Bad section.")
    save_decision("ui-test", decision)
    lineage = build_lineage_event(decision)
    assert lineage["decision"]["type"] == "reject"
    assert lineage["decision"]["reason"] == "Bad section."
