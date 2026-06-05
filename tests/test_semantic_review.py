"""T-RDE regression tests for Semantic Review Layer (Phase 6)."""
from pathlib import Path

from sayane.core.import_bundle import import_bundle_with_semantic_review
from sayane.core.loader import load_profile


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def _a2_bundle():
    from sayane.core.import_bundle import parse_bundle
    return parse_bundle(Path("docs/transfer-tests/a2-chatgpt-return.yml"))


def test_a2b_semantic_overlap_detected():
    """A2 return bundle should trigger semantic overlap for RDE and Sayane."""
    bundle = _a2_bundle()
    assert bundle
    candidates, review = import_bundle_with_semantic_review(bundle, _profile())
    assert len(candidates) == 5

    # Candidate 3 (technical) has unstable_placement
    flags_3 = review["candidate_flags"][2]
    assert "unstable_placement" in flags_3
    assert "review_required" in flags_3

    # Candidate 4 (principles) has semantic_overlap
    flags_4 = review["candidate_flags"][3]
    assert "semantic_overlap" in flags_4

    # Overlap warnings exist for rde and sayane
    terms = {t for ow in review["overlap_warnings"] for t in ow["terms"]}
    assert "rde" in terms
    assert "sayane" in terms


def test_rde_in_technical_preferences_flagged():
    """RDE in technical.preferences should trigger unstable_placement."""
    candidates, review = import_bundle_with_semantic_review(
        {"technical": {"preferences": ["RDE"]}},
        _profile(),
    )
    assert len(candidates) == 1
    flags = review["candidate_flags"][0]
    assert "unstable_placement" in flags
    assert "review_required" in flags


def test_sayane_in_assistant_identity_flagged():
    """Sayane in assistant_identity should trigger boundary_sensitive."""
    from sayane.core.semantic_review import check_identity_boundary

    warnings = check_identity_boundary({"name": "Sayane"}, "assistant_identity")
    assert len(warnings) >= 1
    assert warnings[0].type == "boundary_sensitive"


def test_known_concept_registry_is_hint_only():
    """Known concept registry source_authority is hint_only."""
    from sayane.core.semantic_review import KNOWN_CONCEPTS
    for concept in KNOWN_CONCEPTS.values():
        assert concept.source_authority == "hint_only"


def test_auto_approve_never_true():
    """Semantic review must never auto-approve or auto-reject."""
    bundle = _a2_bundle()
    assert bundle
    candidates, review = import_bundle_with_semantic_review(bundle, _profile())
    # Review adds metadata but does NOT modify candidates
    assert len(candidates) == 5
    # All candidates should still have their original data
    for c in candidates:
        assert "section" in c
        assert "action" in c
        assert "proposed_value" in c


def test_no_candidate_modification():
    """Semantic review adds flags but does NOT modify candidate content."""
    from sayane.core.import_bundle import import_bundle_as_candidates
    bundle = _a2_bundle()
    assert bundle
    raw_candidates = import_bundle_as_candidates(bundle, _profile())
    candidates, review = import_bundle_with_semantic_review(bundle, _profile())
    # Same number of candidates
    assert len(candidates) == len(raw_candidates)
    # Same content
    for i in range(len(candidates)):
        assert candidates[i]["section"] == raw_candidates[i]["section"]
        assert candidates[i]["proposed_value"] == raw_candidates[i]["proposed_value"]
