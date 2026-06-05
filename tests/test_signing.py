"""T-RDE tests for Cryptographic Signing (Phase 16)."""
import tempfile
from pathlib import Path

from sayane.core.signing import (
    canonical_payload,
    generate_keypair,
    sign_data,
    signed_payload_for_bundle,
    verify_signature,
    list_keys,
)


def test_key_generate_creates_ed25519_keypair():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        info = generate_keypair(kd)
        assert info["algorithm"] == "ed25519"
        assert info["key_id"]


def test_key_list_shows_generated_keys():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        generate_keypair(kd)
        keys = list_keys(kd)
        assert len(keys) >= 1


def test_bundle_sign_adds_signature():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        info = generate_keypair(kd)
        data = {"identity": {"name": "Test"}}
        signed = sign_data(data, info["key_id"], payload_fn=signed_payload_for_bundle, key_dir=kd)
        assert signed["signature"]["status"] == "signed"
        assert "value" in signed["signature"]


def test_bundle_verify_valid_signature():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        info = generate_keypair(kd)
        data = {"identity": {"name": "Test"}}
        signed = sign_data(data, info["key_id"], payload_fn=signed_payload_for_bundle, key_dir=kd)
        result = verify_signature(signed, payload_fn=signed_payload_for_bundle, key_dir=kd)
        assert result["status"] == "valid"


def test_bundle_verify_detects_tampering():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        info = generate_keypair(kd)
        data = {"identity": {"name": "Original"}}
        signed = sign_data(data, info["key_id"], payload_fn=signed_payload_for_bundle, key_dir=kd)
        signed["identity"]["name"] = "Tampered"
        result = verify_signature(signed, payload_fn=signed_payload_for_bundle, key_dir=kd)
        assert result["status"] == "invalid"


def test_unsigned_bundle_returns_unsigned_status():
    data = {"identity": {"name": "Test"}}
    result = verify_signature(data, payload_fn=signed_payload_for_bundle)
    assert result["status"] == "unsigned"


def test_canonical_payload_deterministic():
    a = canonical_payload({"b": 1, "a": 2})
    b = canonical_payload({"a": 2, "b": 1})
    assert a == b


def test_signature_field_excluded_from_hash():
    data = {"payload": "test", "signature": {"value": "old"}}
    payload = signed_payload_for_bundle(data)
    assert "signature" not in payload


def test_signature_stable_across_roundtrip():
    with tempfile.TemporaryDirectory() as d:
        kd = Path(d)
        info = generate_keypair(kd)
        data = {"identity": {"name": "Stable"}}
        signed1 = sign_data(data, info["key_id"], payload_fn=signed_payload_for_bundle, key_dir=kd)
        signed2 = sign_data(data, info["key_id"], payload_fn=signed_payload_for_bundle, key_dir=kd)
        assert signed1["signature"]["value"] == signed2["signature"]["value"]
