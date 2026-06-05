"""Context Bundle Provenance and Verification (Phase 9).

Adds bundle metadata, content hash, and verification to context bundles.
Hash: SHA-256 of canonical JSON payload.
Bundle ID: derived from hash.
Import: hard fail on hash mismatch, soft warn on missing metadata.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

# --- Bundle metadata ---


def build_bundle_metadata(
    *,
    transfer_stage: str = "export",
    transfer_path: list[str] | None = None,
    profile_id: str | None = None,
    source_model: str | None = None,
    system_version: str | None = None,
) -> dict[str, Any]:
    """Build provenance metadata for a context bundle."""
    return {
        "bundle_id": "",  # filled after hash
        "schema_version": "0.1.0",
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": {
            "system": "Sayane",
            "version": system_version or "dev",
        },
        "source_profile": {
            "profile_id": profile_id,
        },
        "transfer": {
            "stage": transfer_stage,
            "path": transfer_path or [],
        },
        "llm_memory": False,
        "external_context": True,
        "signature": {
            "status": "unsigned",
            "algorithm": None,
            "key_id": None,
            "value": None,
        },
    }


# --- Content hashing ---


def canonical_json(data: dict[str, Any]) -> str:
    """Produce a canonical JSON string with sorted keys."""
    return json.dumps(data, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def compute_bundle_hash(payload: dict[str, Any]) -> str:
    """Compute SHA-256 hash of a bundle's content payload.

    Excludes the hash field and signature value to avoid recursion.
    """
    # Deep copy and strip hash/signature fields for clean computation
    clean = {k: v for k, v in payload.items() if k not in ("content_hash", "metadata")}
    canonical = canonical_json(clean)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_bundle_id(content_hash: str) -> str:
    return f"bundle-sha256-{content_hash[:16]}"


# --- Verification ---


class BundleVerification:
    def __init__(self, status: str, bundle_id: str = "", details: str = ""):
        self.status = status  # "verified" | "unverified" | "failed"
        self.bundle_id = bundle_id
        self.details = details
        self.hash_value: str = ""
        self.signature_status: str = "unsigned"


def verify_bundle(payload: dict[str, Any]) -> BundleVerification:
    """Verify a bundle's content hash and provenance metadata.

    Returns BundleVerification with status and details.
    """
    meta = payload.get("metadata")
    content_hash = payload.get("content_hash")

    result = BundleVerification(status="unverified")

    # Check metadata boundary
    if isinstance(meta, dict):
        llm_memory = meta.get("llm_memory", True)
        external = meta.get("external_context", False)
        if llm_memory is not False or external is not True:
            result.details += (
                "Bundle metadata claims LLM memory or internal context. "
                "Expected llm_memory=false and external_context=true. "
            )

    # Check hash
    if content_hash:
        expected = content_hash.get("value") if isinstance(content_hash, dict) else str(content_hash)
        computed = compute_bundle_hash(payload)
        result.hash_value = computed
        if expected == computed:
            result.status = "verified"
            bundle_id = content_hash.get("bundle_id") if isinstance(content_hash, dict) else None
            result.bundle_id = bundle_id or generate_bundle_id(computed)
        else:
            result.status = "failed"
            result.details += f"Hash mismatch: expected={expected[:16]}... computed={computed[:16]}..."
    else:
        result.details += "Bundle hash is missing."
        result.hash_value = compute_bundle_hash(payload)
        result.bundle_id = generate_bundle_id(result.hash_value)

    # Check signature status
    if isinstance(meta, dict):
        sig = meta.get("signature", {})
        if isinstance(sig, dict):
            result.signature_status = sig.get("status", "unsigned")

    return result


def verify_and_require_pass(payload: dict[str, Any]) -> tuple[bool, str]:
    """Verify bundle. Returns (allowed, message).

    Hard fail: hash present but mismatch.
    Soft warn: hash missing, metadata missing, unsigned.
    """
    result = verify_bundle(payload)
    if result.status == "failed":
        return False, f"Bundle verification failed: {result.details}"
    if result.status == "unverified":
        return True, f"Warning: {result.details}"
    return True, f"Verified: {result.bundle_id}"
