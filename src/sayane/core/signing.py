"""Cryptographic Signing Enforcement (Phase 16).

Ed25519-based signing and verification for bundles, audit exports,
and policy files. Local-first, no CA, no remote trust.
"""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

# --- Key management ---

DEFAULT_KEY_DIR = Path.home() / ".sayane" / "keys"


def generate_keypair(key_dir: Path | None = None) -> dict[str, Any]:
    """Generate an Ed25519 keypair. Returns key metadata dict."""
    key_dir = key_dir or DEFAULT_KEY_DIR
    key_dir.mkdir(parents=True, exist_ok=True)

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    key_id = uuid4().hex[:12]
    now = datetime.now(UTC).isoformat()

    # Serialize private key
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    priv_path = key_dir / f"{key_id}.key"
    pub_path = key_dir / f"{key_id}.pub"

    priv_path.write_bytes(priv_bytes)
    os.chmod(priv_path, 0o600)
    pub_path.write_bytes(pub_bytes)

    return {
        "key_id": key_id,
        "algorithm": "ed25519",
        "created_at": now,
        "private_key_path": str(priv_path),
        "public_key_path": str(pub_path),
    }


def load_private_key(key_id: str, key_dir: Path | None = None) -> ed25519.Ed25519PrivateKey | None:
    key_dir = key_dir or DEFAULT_KEY_DIR
    path = key_dir / f"{key_id}.key"
    if not path.exists():
        return None
    data = path.read_bytes()
    return ed25519.Ed25519PrivateKey.from_private_bytes(data) if b"PRIVATE" not in data else serialization.load_pem_private_key(data, password=None)  # type: ignore[return-value]


def load_public_key(key_id: str, key_dir: Path | None = None) -> ed25519.Ed25519PublicKey | None:
    key_dir = key_dir or DEFAULT_KEY_DIR
    path = key_dir / f"{key_id}.pub"
    if not path.exists():
        return None
    data = path.read_bytes()
    return ed25519.Ed25519PublicKey.from_public_bytes(data) if b"PUBLIC" not in data else serialization.load_pem_public_key(data)  # type: ignore[return-value]


def list_keys(key_dir: Path | None = None) -> list[dict[str, str]]:
    key_dir = key_dir or DEFAULT_KEY_DIR
    if not key_dir.is_dir():
        return []
    keys: list[dict[str, str]] = []
    for f in sorted(key_dir.glob("*.pub")):
        key_id = f.stem
        pub_path = f
        priv_path = key_dir / f"{key_id}.key"
        keys.append({
            "key_id": key_id,
            "has_private": str(priv_path.exists()),
            "public_key_path": str(pub_path),
        })
    return keys


# --- Canonical payload ---

def canonical_payload(data: dict[str, Any]) -> str:
    """Canonical JSON for signing — stable key order, no whitespace."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def signed_payload_for_bundle(bundle: dict[str, Any]) -> str:
    clean = {k: v for k, v in bundle.items() if k != "signature"}
    return canonical_payload(clean)


# --- Signing ---

def sign_data(data: dict[str, Any], key_id: str, payload_fn=None, key_dir: Path | None = None) -> dict[str, Any]:
    """Sign a data dict, returning it with signature field added."""
    private_key = load_private_key(key_id, key_dir)
    if private_key is None:
        raise ValueError(f"Private key not found: {key_id}")

    payload = payload_fn(data) if payload_fn else canonical_payload(data)
    sig_bytes = private_key.sign(payload.encode("utf-8"))

    result = dict(data)
    result["signature"] = {
        "status": "signed",
        "algorithm": "ed25519",
        "key_id": key_id,
        "signed_at": datetime.now(UTC).isoformat(),
        "value": sig_bytes.hex(),
    }
    return result


def verify_signature(data: dict[str, Any], payload_fn=None, key_dir: Path | None = None) -> dict[str, Any]:
    """Verify a signature on data. Returns status dict."""
    sig = data.get("signature", {})
    if not isinstance(sig, dict) or sig.get("status") != "signed":
        return {"status": "unsigned", "message": "No signature present."}

    key_id = sig.get("key_id", "")
    sig_hex = sig.get("value", "")
    if not key_id or not sig_hex:
        return {"status": "invalid", "message": "Incomplete signature metadata."}

    public_key = load_public_key(key_id, key_dir)
    if public_key is None:
        return {"status": "invalid", "message": f"Public key not found: {key_id}"}

    try:
        sig_bytes = bytes.fromhex(sig_hex)
    except ValueError:
        return {"status": "invalid", "message": "Malformed signature value."}

    payload = payload_fn(data) if payload_fn else canonical_payload(data)
    try:
        public_key.verify(sig_bytes, payload.encode("utf-8"))
        return {"status": "valid", "key_id": key_id, "algorithm": sig.get("algorithm", "unknown")}
    except InvalidSignature:
        return {"status": "invalid", "message": "Signature verification failed — data may be tampered."}
