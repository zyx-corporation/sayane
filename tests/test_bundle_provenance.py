"""T-RDE tests for Bundle Provenance & Verification (Phase 9)."""
import json
from pathlib import Path

from sayane.core.bundle_provenance import (
    BundleVerification,
    build_bundle_metadata,
    canonical_json,
    compute_bundle_hash,
    generate_bundle_id,
    verify_and_require_pass,
    verify_bundle,
)


def test_build_bundle_metadata():
    meta = build_bundle_metadata(
        transfer_stage="export",
        transfer_path=["Sayane", "ChatGPT"],
        profile_id="default",
    )
    assert meta["llm_memory"] is False
    assert meta["external_context"] is True
    assert meta["transfer"]["stage"] == "export"
    assert meta["transfer"]["path"] == ["Sayane", "ChatGPT"]
    assert meta["signature"]["status"] == "unsigned"


def test_canonical_json_deterministic():
    """Canonical JSON must be deterministic — same payload = same string."""
    a = canonical_json({"b": 1, "a": 2})
    b = canonical_json({"a": 2, "b": 1})
    assert a == b


def test_bundle_hash_deterministic():
    """Same payload must produce the same hash regardless of key order."""
    p1 = {"name": "Test", "values": ["a", "b"]}
    p2 = {"values": ["a", "b"], "name": "Test"}
    assert compute_bundle_hash(p1) == compute_bundle_hash(p2)


def test_bundle_hash_changes_with_content():
    h1 = compute_bundle_hash({"x": 1})
    h2 = compute_bundle_hash({"x": 2})
    assert h1 != h2


def test_bundle_id_from_hash():
    h = compute_bundle_hash({"test": True})
    bid = generate_bundle_id(h)
    assert bid.startswith("bundle-sha256-")
    assert len(bid) == 16 + len("bundle-sha256-")


def test_verify_missing_hash_warns():
    """Bundle without hash should be unverified but allowed."""
    payload = {"identity": {"name": "Test"}}
    allowed, msg = verify_and_require_pass(payload)
    assert allowed is True
    assert "Warning" in msg


def test_verify_matching_hash_passes():
    """Bundle with correct hash should verify."""
    payload = {"identity": {"name": "Test"}}
    h = compute_bundle_hash(payload)
    payload["content_hash"] = {"algorithm": "sha256", "value": h}
    allowed, msg = verify_and_require_pass(payload)
    assert allowed is True
    assert "Verified" in msg


def test_verify_mismatched_hash_fails():
    """Bundle with wrong hash should be rejected."""
    payload = {"identity": {"name": "Test"}}
    payload["content_hash"] = {"algorithm": "sha256", "value": "0" * 64}
    allowed, msg = verify_and_require_pass(payload)
    assert allowed is False
    assert "failed" in msg.lower()


def test_unsigned_signature_allowed():
    meta = build_bundle_metadata()
    assert meta["signature"]["status"] == "unsigned"


def test_import_allows_old_bundle_without_metadata():
    """Backward compatibility: import old bundles without metadata."""
    payload = {"identity": {"name": "OldBundle"}}
    # No metadata, no hash — should be allowed with warning
    result = verify_bundle(payload)
    assert result.status == "unverified"
    allowed, msg = verify_and_require_pass(payload)
    assert allowed is True
