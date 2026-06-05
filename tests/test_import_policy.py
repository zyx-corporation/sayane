"""T-RDE tests for Import Policy Profiles (Phase 11)."""
from sayane.core.import_policy import (
    DEFAULT_POLICY,
    evaluate_policy,
    get_policy,
    list_policies,
)


def test_policy_list_contains_builtin_profiles():
    names = list_policies()
    assert "strict" in names
    assert "standard" in names
    assert "legacy_compatible" in names
    assert "development" in names


def test_default_policy_is_standard():
    assert DEFAULT_POLICY == "standard"


def test_standard_allows_missing_hash_with_warning():
    result = evaluate_policy("standard", verification_status="unverified")
    assert result.import_allowed is True
    assert result.status == "WARN"


def test_strict_blocks_missing_hash():
    result = evaluate_policy("strict", verification_status="unverified")
    assert result.import_allowed is False
    assert result.status == "BLOCK"


def test_hash_mismatch_always_blocks():
    for policy in ["strict", "standard", "legacy_compatible", "development"]:
        result = evaluate_policy(policy, verification_status="failed")
        assert result.import_allowed is False
        assert result.status == "BLOCK"


def test_standard_blocks_boundary_sensitive():
    result = evaluate_policy("standard", semantic_flags=["boundary_sensitive"])
    assert result.import_allowed is False
    assert result.status == "BLOCK"


def test_legacy_allows_boundary_sensitive_with_warning():
    result = evaluate_policy("legacy_compatible", semantic_flags=["boundary_sensitive"])
    assert result.import_allowed is True
    assert result.status == "WARN"


def test_development_allows_missing_metadata():
    result = evaluate_policy("development", verification_status="unverified")
    assert result.import_allowed is True
    assert result.status == "PASS"  # allow = no warn


def test_policy_does_not_auto_approve():
    result = evaluate_policy("standard", semantic_flags=["review_required"])
    # Policy only decides import_allowed, never auto-approves candidates
    assert result.review_allowed is True  # human can always review
    assert result.apply_allowed == result.import_allowed


def test_unknown_policy_blocks():
    result = evaluate_policy("nonexistent")
    assert result.import_allowed is False
    assert result.status == "BLOCK"


def test_get_policy_returns_profile():
    p = get_policy("strict")
    assert p is not None
    assert p["name"] == "strict"
    assert "semantic_review" in p
    assert p["semantic_review"]["boundary_sensitive"] == "block"
