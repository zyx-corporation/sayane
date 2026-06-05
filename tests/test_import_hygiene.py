"""Tests for import hygiene — placeholder and empty filtering (#156)."""
from pathlib import Path

from sayane.core.import_bundle import (
    _contains_placeholder_identity,
    _is_empty_proposal,
    _is_placeholder_value,
    import_bundle_as_candidates,
)
from sayane.core.loader import load_profile


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


# --- Placeholder detection ---

def test_placeholder_value_detection():
    assert _is_placeholder_value("Example User") is True
    assert _is_placeholder_value("example") is True
    assert _is_placeholder_value("developer") is True
    assert _is_placeholder_value("test user") is True
    assert _is_placeholder_value("sample user") is True


def test_real_value_not_placeholder():
    assert _is_placeholder_value("Tomoyuki Kano") is False
    assert _is_placeholder_value("tomyuk") is False
    assert _is_placeholder_value("代表") is False
    assert _is_placeholder_value("RDE") is False
    assert _is_placeholder_value("") is False  # empty is handled separately


def test_contains_placeholder_identity():
    assert _contains_placeholder_identity({"name": "Example User"}) is True
    assert _contains_placeholder_identity({"name": "Real Name"}) is False
    assert _contains_placeholder_identity({"preferred_name": "developer"}) is True
    assert _contains_placeholder_identity({"roles": ["developer", "test"]}) is True


# --- Empty proposal detection ---

def test_empty_proposal_detection():
    assert _is_empty_proposal(None) is True
    assert _is_empty_proposal("") is True
    assert _is_empty_proposal({}) is True
    assert _is_empty_proposal([]) is True
    assert _is_empty_proposal("  ") is True


def test_non_empty_proposal():
    assert _is_empty_proposal("hello") is False
    assert _is_empty_proposal({"key": "value"}) is False
    assert _is_empty_proposal(["item"]) is False
    assert _is_empty_proposal(0) is False


# --- Import integration ---

def test_placeholder_identity_skipped():
    candidates = import_bundle_as_candidates(
        {"identity": {"name": "Example User", "preferred_name": "example", "roles": ["developer"]}},
        _profile(),
    )
    # Should NOT generate identity candidate
    ident = [c for c in candidates if c["section"] == "identity"]
    assert len(ident) == 0


def test_empty_execution_context_skipped():
    candidates = import_bundle_as_candidates(
        {"execution_context": {}},
        _profile(),
    )
    exec_ctx = [c for c in candidates if c["section"] == "execution_context"]
    assert len(exec_ctx) == 0


def test_valid_identity_still_works():
    candidates = import_bundle_as_candidates(
        {"identity": {"name": "Real Name", "preferred_name": "real"}},
        _profile(),
    )
    ident = [c for c in candidates if c["section"] == "identity"]
    assert len(ident) == 1
    assert ident[0]["action"] == "update"


def test_valid_section_still_works():
    candidates = import_bundle_as_candidates(
        {"important_terms": ["NewTerm"]},
        _profile(),
    )
    assert len(candidates) == 1
    assert candidates[0]["section"] == "important_terms"


def test_empty_list_not_erase():
    candidates = import_bundle_as_candidates(
        {"important_terms": []},
        _profile(),
    )
    assert len(candidates) == 0  # Empty list → skip, no silent erase
