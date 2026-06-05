"""Tests for context bundle import (#143)."""
from pathlib import Path

from sayane.core.import_bundle import import_bundle_as_candidates, parse_bundle
from sayane.core.loader import load_profile


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def test_parse_yaml_bundle():
    bundle = parse_bundle(Path("examples/profiles/minimal.yaml"))
    assert bundle is not None
    assert "identity" in bundle


def test_import_no_diff_same_profile():
    bundle = parse_bundle(Path("examples/profiles/minimal.yaml"))
    assert bundle
    candidates = import_bundle_as_candidates(bundle, _profile())
    assert candidates == []


def test_import_detects_identity_change():
    candidates = import_bundle_as_candidates(
        {"identity": {"name": "New Name", "preferred_name": "new"}},
        _profile(),
    )
    assert len(candidates) >= 1
    ident = next(c for c in candidates if c["section"] == "identity")
    assert ident["action"] == "update"


def test_import_detects_new_section():
    candidates = import_bundle_as_candidates(
        {"important_terms": ["RDE", "Sayane", "NewTerm"]},
        _profile(),
    )
    assert len(candidates) >= 1
    assert candidates[0]["section"] == "important_terms"
    assert candidates[0]["action"] == "add"
