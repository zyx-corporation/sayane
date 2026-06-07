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


# --- Package Import Preview (F-4) ---

def preview_package(package_dir: Path) -> dict[str, Any]:
    """Preview a package without importing or modifying any profile."""
    manifest = inspect_package(package_dir)
    verified = verify_package(package_dir)

    preview: dict[str, Any] = {
        "profile_modified": False,
        "preview_only": True,
        "package": {
            "package_id": manifest.get("package_id") if manifest else None,
            "verification_status": verified["status"],
            "artifact_count": len(manifest.get("artifacts", [])) if manifest else 0,
            "signed_artifacts": manifest.get("summary", {}).get("signed_artifacts", 0) if manifest else 0,
            "unsigned_artifacts": manifest.get("summary", {}).get("unsigned_artifacts", 0) if manifest else 0,
            "invalid_artifacts": manifest.get("summary", {}).get("invalid_artifacts", 0) if manifest else 0,
        },
        "artifacts": [],
        "scoped_contexts": [],
        "audit_summary": {"approve": 0, "reject": 0, "modify": 0, "defer": 0, "scoped_accept": 0},
        "policy": {"source": "built_in", "name": manifest.get("policy", {}).get("profile", "standard") if manifest else "unknown", "status": "UNKNOWN"},
        "risks": {"critical": [], "warnings": []},
        "errors": verified.get("errors", []),
        "warnings": verified.get("warnings", []),
    }

    # Artifacts
    for art in (manifest or {}).get("artifacts", []):
        art_path = package_dir / art.get("path", "")
        exists = art_path.exists()
        hash_val = art.get("hash", {}).get("value", "")
        sig_status = art.get("signature", {}).get("status", "unsigned")

        preview["artifacts"].append({
            "role": art.get("role", "other"),
            "path": art.get("path", ""),
            "hash_status": "verified" if (exists and hash_val and _hash_file(art_path) == hash_val) else ("unverified" if exists else "missing"),
            "signature_status": sig_status,
        })

    # Scoped contexts from audit export
    audit_path = None
    for art in (manifest or {}).get("artifacts", []):
        if art.get("role") == "audit_export":
            audit_path = package_dir / art.get("path", "")
    if audit_path and audit_path.exists():
        try:
            audit_data = json.loads(audit_path.read_text(encoding="utf-8"))
            for rec in audit_data.get("records", []):
                dec = rec.get("decision", {})
                if dec.get("type") == "scoped_accept":
                    scoped = rec.get("scoped_accept") or {}
                    entry = {
                        "candidate_id": rec.get("candidate", {}).get("id", "?"),
                        "decision": "scoped_accept",
                        "accepted_scope": scoped.get("accepted_scope", {"level": "未指定"}),
                        "conditions": scoped.get("conditions", []),
                        "negative_constraints": scoped.get("negative_constraints", []),
                        "promotion_policy": scoped.get("promotion_policy"),
                        "reuse_policy": scoped.get("reuse_policy"),
                    }
                    preview["scoped_contexts"].append(entry)
                d_type = dec.get("type", "")
                if d_type in preview["audit_summary"]:
                    preview["audit_summary"][d_type] += 1
        except Exception:
            pass

    # Risks
    if verified["status"] == "FAILED":
        preview["risks"]["critical"].append({"code": "verification_failed", "message": "Package verification failed."})
    if preview["package"]["unsigned_artifacts"] > 0:
        preview["risks"]["warnings"].append({"code": "unsigned_artifact", "message": "Unsigned artifacts present."})
    if preview["scoped_contexts"]:
        preview["risks"]["warnings"].append({"code": "scoped_context_requires_review", "message": "Scoped context entries require review before reuse."})

    return preview


def render_preview_text(preview: dict[str, Any]) -> str:
    """Render preview as human-readable text."""
    pkg = preview["package"]
    lines = [
        "=== Sayane Package Preview ===",
        "",
        "Package:",
        f"  ID: {pkg['package_id'] or 'N/A'}",
        f"  Status: {pkg['verification_status']}",
        f"  Artifacts: {pkg['artifact_count']}",
        f"  Signed: {pkg['signed_artifacts']}",
        f"  Unsigned: {pkg['unsigned_artifacts']}",
        f"  Invalid: {pkg['invalid_artifacts']}",
        "",
        "Artifacts:",
    ]
    for art in preview["artifacts"]:
        lines.append(f"  - {art['role']}: {art['path']}")
        lines.append(f"    hash: {art['hash_status']}, sig: {art['signature_status']}")

    lines.append("")
    lines.append("Scoped Context:")
    if preview["scoped_contexts"]:
        for sc in preview["scoped_contexts"]:
            scope = sc.get("accepted_scope", {})
            lines.append(f"  - {sc['candidate_id']}: {scope.get('level', '?')}:{scope.get('target', '?')}:{scope.get('sub_scope', '?')}")
            for c in sc.get("conditions", []):
                lines.append(f"    condition: {c}")
            for nc in sc.get("negative_constraints", []):
                lines.append(f"    constraint: {nc}")
    else:
        lines.append("  (none)")

    lines.append("")
    lines.append("Audit Decisions:")
    for k, v in preview["audit_summary"].items():
        lines.append(f"  {k}: {v}")

    lines.append("")
    lines.append("Policy:")
    pol = preview["policy"]
    lines.append(f"  active: {pol['name']}, result: {pol['status']}")

    lines.append("")
    lines.append("Risk Summary:")
    if preview["risks"]["critical"]:
        lines.append("  Critical:")
        for r in preview["risks"]["critical"]:
            lines.append(f"    - {r['message']}")
    if preview["risks"]["warnings"]:
        lines.append("  Warnings:")
        for w in preview["risks"]["warnings"]:
            lines.append(f"    - {w['message']}")

    lines.append("")
    lines.append("Boundary:")
    lines.append("  This is a preview only. No profile has been modified.")
    lines.append("  Verified packages are not automatically accepted.")

    return "\n".join(lines)
