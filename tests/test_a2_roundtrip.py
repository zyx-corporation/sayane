"""Tests for A2 round-trip import (#142)."""
from pathlib import Path

from sayane.core.import_bundle import (
    ImportMetadata,
    import_bundle_as_candidates,
    parse_bundle,
)
from sayane.core.loader import load_profile

FIXTURE_RETURN = Path(__file__).resolve().parent / "fixtures" / "context_portability" / "a2_chatgpt_return.yml"


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def test_parse_return_bundle_metadata():
    bundle = parse_bundle(FIXTURE_RETURN)
    assert bundle is not None
    meta = bundle.get("metadata")
    assert meta is not None
    assert meta["source"] == "chatgpt_roundtrip"
    assert meta["llm_memory"] is False
    assert meta["roundtrip_stage"] == "A2"


def test_identity_is_duplicate_confirmed():
    """Identity name/preferred_name should match stored profile — no candidate."""
    bundle = parse_bundle(FIXTURE_RETURN)
    assert bundle
    candidates = import_bundle_as_candidates(bundle, _profile())
    # identity section should NOT appear because name/roles are identical
    ident_candidates = [c for c in candidates if c["section"] == "identity"]
    assert len(ident_candidates) == 0


def test_return_bundle_generates_candidates_for_new_sections():
    """Unrecognized sections (writing, principles) become candidates."""
    bundle = parse_bundle(FIXTURE_RETURN)
    assert bundle
    candidates = import_bundle_as_candidates(bundle, _profile())
    # writing section is new
    writing = [c for c in candidates if c["section"] == "writing"]
    assert len(writing) >= 1
    assert writing[0]["action"] == "add"


def test_return_bundle_parses_metadata_for_lineage():
    bundle = parse_bundle(FIXTURE_RETURN)
    assert bundle
    meta = bundle.get("metadata", {})
    assert meta.get("uncertainty") == "items are candidates, not canonical facts"


def test_import_does_not_mutate_profile_directly():
    """Importing a bundle must NOT write to profile — only generate candidates."""
    bundle = parse_bundle(FIXTURE_RETURN)
    assert bundle
    profile = _profile()
    candidates = import_bundle_as_candidates(bundle, profile)
    # Verify profile is unchanged
    assert profile.identity.name == "Example User"
    # Candidates exist but profile is untouched
    assert len(candidates) > 0
