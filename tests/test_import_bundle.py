"""Tests for import-to-Candidate Review flow (#143)."""
import json
from pathlib import Path

from sayane.core.import_bundle import (
    ImportMetadata,
    create_import_candidates,
    import_bundle_as_candidates,
    parse_bundle,
)
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


def test_same_value_no_duplicate_candidate():
    """Same targetPath + same value should produce no candidate."""
    candidates = import_bundle_as_candidates(
        {"identity": {"name": "Example User", "preferred_name": "example", "roles": ["developer"]}},
        _profile(),
    )
    assert candidates == []


def test_create_import_candidates_generates_records():
    meta = ImportMetadata(import_id="test-import", source_path="bundle.yaml")
    candidates = create_import_candidates(
        {"identity": {"name": "Imported User"}},
        _profile(),
        import_meta=meta,
    )
    assert len(candidates) == 1
    c = candidates[0]
    assert c.status == "pending"
    assert c.proposal.section == "identity"
    assert c.storage_policy is not None
    assert c.storage_policy.target_path == "identity"


def test_import_markdown_bundle():
    md = """# Sayane Context Bundle

Target: generic
Scopes: identity

## Identity

- Name: Markdown User
- Preferred name: md
- Roles: tester
"""
    from sayane.core.import_bundle import _parse_markdown_bundle
    bundle = _parse_markdown_bundle(md)
    assert bundle
    ident = bundle.get("identity", {})
    assert ident.get("name") == "Markdown User"


def test_create_import_candidates_preserves_metadata():
    meta = ImportMetadata(
        import_id="meta-test",
        source_path="/tmp/bundle.yaml",
        source_format="yaml",
        source_target="chatgpt",
        source_scopes=["identity", "interaction"],
    )
    candidates = create_import_candidates(
        {"identity": {"name": "Meta User"}},
        _profile(),
        import_meta=meta,
    )
    assert len(candidates) == 1
    assert candidates[0].source.type == "bundle_import/yaml"
    assert candidates[0].source.uri == "/tmp/bundle.yaml"
    assert candidates[0].parent_capture_id == "meta-test"
