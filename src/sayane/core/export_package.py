"""Signed Export Package (Phase 17).

Packages context bundles, audit exports, transfer reports, and policy
files into a verifiable directory package with manifest, hashes, and
optional signatures.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.core.signing import sign_data, verify_signature, canonical_payload

SCHEMA_VERSION = "sayane-export-package-v1"


# --- Package manifest ---

def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_package_manifest(
    artifacts: dict[str, Path],
    policy_profile: str = "standard",
    purpose: str = "audit_handoff",
) -> dict[str, Any]:
    """Build a package manifest from artifact paths."""
    artifact_entries: list[dict[str, Any]] = []
    artifact_roles = {
        "bundle.yml": "context_bundle",
        "audit-export.json": "audit_export",
        "audit-export.md": "audit_export",
        "transfer-regression-report.json": "transfer_report",
        "transfer-regression-report.md": "transfer_report",
        "policy.yaml": "policy_file",
        "policy.yml": "policy_file",
    }

    signed_count = unsigned_count = 0
    for path in sorted(artifacts.values()):
        fname = path.name
        role = artifact_roles.get(fname, "other")
        h = _hash_file(path)

        # Check if signature file exists
        sig_path = path.parent / f"{fname}.sig"
        sig_status: dict[str, Any] = {"status": "unsigned"}
        if sig_path.exists():
            sig_status = {"status": "signed", "algorithm": "unknown", "signature_path": str(sig_path)}
            signed_count += 1
        else:
            unsigned_count += 1

        entry: dict[str, Any] = {
            "id": f"artifact-{role}",
            "role": role,
            "path": f"artifacts/{fname}",
            "hash": {"algorithm": "sha256", "value": h},
            "signature": sig_status,
        }

        # Try to extract provenance for bundles
        if role == "context_bundle":
            try:
                import yaml
                bundle_data = yaml.safe_load(path.read_text(encoding="utf-8"))
                if isinstance(bundle_data, dict):
                    meta = bundle_data.get("metadata", {})
                    if isinstance(meta, dict):
                        transfer = meta.get("transfer", {})
                        entry["provenance"] = {
                            "transfer_path": transfer.get("path", []) if isinstance(transfer, dict) else [],
                        }
            except Exception:
                pass

        artifact_entries.append(entry)

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_id": "",  # filled after hash
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": {"tool": "sayane", "version": None},
        "purpose": purpose,
        "artifacts": artifact_entries,
        "policy": {"profile": policy_profile},
        "summary": {
            "artifact_count": len(artifact_entries),
            "signed_artifacts": signed_count,
            "unsigned_artifacts": unsigned_count,
            "invalid_artifacts": 0,
        },
    }

    # Compute package ID from canonical manifest
    clean = {k: v for k, v in manifest.items() if k not in ("package_id", "signature")}
    pkg_hash = hashlib.sha256(canonical_payload(clean).encode("utf-8")).hexdigest()
    manifest["package_id"] = f"pkg-sha256-{pkg_hash[:16]}"

    return manifest


# --- Package create ---

README_TEMPLATE = """# Sayane Export Package

This package contains Sayane context transfer and audit artifacts.

## Contents

- Context bundle
- Audit export
- Transfer report
- Policy file
- Manifest

## Verification

```bash
sayane package verify .
```

## Boundary

This package preserves artifacts and their verification metadata.
It does not prove that the content is true.
It does not imply automatic acceptance of any candidate.
"""


def create_package(
    output_dir: Path,
    artifacts: dict[str, Path],
    policy_profile: str = "standard",
    sign: bool = False,
    key_id: str | None = None,
) -> dict[str, Any]:
    """Create a signed export package directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts_dir = output_dir / "artifacts"
    artifacts_dir.mkdir(exist_ok=True)

    # Copy artifacts
    copied: dict[str, Path] = {}
    for name, src in artifacts.items():
        dst = artifacts_dir / src.name
        shutil.copy2(src, dst)
        copied[name] = dst

    # Copy signature files if present
    sigs_dir = output_dir / "signatures"
    sigs_dir.mkdir(exist_ok=True)
    for src in artifacts.values():
        sig = src.parent / f"{src.name}.sig"
        if sig.exists():
            shutil.copy2(sig, sigs_dir / sig.name)

    manifest = build_package_manifest(copied, policy_profile=policy_profile)

    # Sign manifest if requested
    if sign and key_id:
        manifest = sign_data(manifest, key_id)

    # Write manifest
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Write README
    (output_dir / "README.md").write_text(README_TEMPLATE, encoding="utf-8")

    return manifest


# --- Package inspect ---

def inspect_package(package_dir: Path) -> dict[str, Any] | None:
    """Inspect a package directory."""
    manifest_path = package_dir / "manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


# --- Package verify ---

def verify_package(package_dir: Path) -> dict[str, Any]:
    """Verify a package directory. Returns status dict."""
    manifest = inspect_package(package_dir)
    if manifest is None:
        return {"status": "FAILED", "errors": ["Manifest missing or invalid."], "warnings": []}

    errors: list[str] = []
    warnings: list[str] = []

    # Verify schema
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"Unsupported schema: {manifest.get('schema_version')}")

    # Verify artifacts
    for art in manifest.get("artifacts", []):
        art_path = package_dir / art.get("path", "")
        if not art_path.exists():
            errors.append(f"Missing artifact: {art.get('path')}")
            continue

        expected_hash = art.get("hash", {}).get("value", "")
        actual_hash = _hash_file(art_path)
        if expected_hash != actual_hash:
            errors.append(f"Hash mismatch: {art.get('path')}")

        sig_status = art.get("signature", {}).get("status", "unsigned")
        if sig_status == "unsigned":
            warnings.append(f"Unsigned artifact: {art.get('path')}")

    # Verify manifest signature
    sig = manifest.get("signature", {})
    if sig.get("status") == "signed":
        result = verify_signature(manifest)
        if result["status"] != "valid":
            errors.append("Manifest signature invalid.")

    status = "FAILED" if errors else "VERIFIED_WITH_WARNINGS" if warnings else "VERIFIED"
    return {"status": status, "errors": errors, "warnings": warnings, "manifest": manifest}
