"""Signed Export Package (Phase 17).

Packages context bundles, audit exports, transfer reports, and policy
files into a verifiable directory package with manifest, hashes, and
optional signatures.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from sayane import __version__
from sayane.core.audit_export import build_export
from sayane.core.audit_trail import AuditStore
from sayane.core.bundle_provenance import (
    build_bundle_metadata,
    compute_bundle_hash,
    generate_bundle_id,
)
from sayane.core.export_scope import pick_profile_sections
from sayane.core.models import SayaneProfile
from sayane.core.signing import sign_data, verify_signature, canonical_payload

SCHEMA_VERSION = "sayane-export-package-v1"
DEFAULT_PACKAGE_KIND = "generic_export_package"
VAULT_AWARE_PACKAGE_KIND = "vault_aware_external_package"
DEFAULT_EXPORT_SCOPES = (
    "identity",
    "interaction",
    "technical",
    "knowledge",
    "projects",
    "terms",
)
RETENTION_CLASS_RULES: dict[str, dict[str, Any]] = {
    "reviewable_context_bundle": {
        "recommended_max_age": "30d",
        "delete_after_import_or_review": True,
        "review_required_before_merge": True,
        "contains_canonical_profile_state": False,
    },
    "redacted_audit_export": {
        "recommended_max_age": "14d",
        "delete_after_import_or_review": True,
        "review_required_before_merge": True,
        "contains_canonical_profile_state": False,
    },
}
VAULT_AWARE_BOUNDARY_DEFAULTS: dict[str, Any] = {
    "storage_boundary": VAULT_AWARE_PACKAGE_KIND,
    "canonical_profile_state": False,
    "review_required_before_merge": True,
    "legacy_compatibility_path": False,
    "import_contract": "preview_only",
    "profile_mutation_allowed": False,
    "candidate_persistence_allowed": False,
    "reserved_future_mutating_workflow": "separate_explicit_review_queue_import",
    "retention_expiry_mode": "warning_only",
    "supported_operator_actions": [
        "offline_review",
        "candidate_generation_preview",
        "manual_redacted_handoff",
    ],
    "forbidden_workflows": [
        "canonical_working_store",
        "automatic_external_sync_promotion",
        "automatic_bidirectional_sync",
        "implicit_filesystem_git_auto_commit_as_primary_sync",
        "direct_profile_merge_without_review",
        "long_lived_unreviewed_archive",
    ],
}


# --- Package manifest ---

def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _retention_policy_for_role(role: str) -> dict[str, Any] | None:
    if role == "context_bundle":
        return {
            "retention_class": "reviewable_context_bundle",
            **RETENTION_CLASS_RULES["reviewable_context_bundle"],
        }
    if role == "audit_export":
        return {
            "retention_class": "redacted_audit_export",
            **RETENTION_CLASS_RULES["redacted_audit_export"],
        }
    return None


def _parse_duration_days(raw: str) -> int | None:
    value = raw.strip().lower()
    if not value:
        return None
    if value.endswith("d") and value[:-1].isdigit():
        return int(value[:-1])
    return None


def _is_retention_expired(created_at: str | None, recommended_max_age: str | None) -> bool:
    if not created_at or not recommended_max_age:
        return False
    days = _parse_duration_days(recommended_max_age)
    if days is None:
        return False
    try:
        created = datetime.fromisoformat(created_at)
    except ValueError:
        return False
    now = datetime.now(UTC)
    if created.tzinfo is None:
        created = created.replace(tzinfo=UTC)
    return (now - created).days > days


def _normalize_boundary(package_kind: str, boundary: dict[str, Any] | None) -> dict[str, Any]:
    normalized = dict(boundary or {})
    if package_kind == VAULT_AWARE_PACKAGE_KIND:
        for key, value in VAULT_AWARE_BOUNDARY_DEFAULTS.items():
            normalized.setdefault(key, value)
    return normalized


def build_package_manifest(
    artifacts: dict[str, Path],
    policy_profile: str = "standard",
    purpose: str = "audit_handoff",
    package_kind: str = DEFAULT_PACKAGE_KIND,
    boundary: dict[str, Any] | None = None,
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
        retention = _retention_policy_for_role(role)
        if retention is not None:
            entry["retention"] = retention

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

    normalized_boundary = _normalize_boundary(package_kind, boundary)
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "package_id": "",  # filled after hash
        "package_kind": package_kind,
        "created_at": datetime.now(UTC).isoformat(),
        "created_by": {"tool": "sayane", "version": None},
        "purpose": purpose,
        "boundary": normalized_boundary,
        "artifacts": artifact_entries,
        "policy": {"profile": policy_profile},
        "retention": {
            "package_class": "reviewable_external_exchange",
            "recommended_max_age": "30d",
            "delete_after_import_or_review": True,
            "artifact_classes": sorted(
                {
                    artifact["retention"]["retention_class"]
                    for artifact in artifact_entries
                    if isinstance(artifact.get("retention"), dict)
                    and artifact["retention"].get("retention_class")
                }
            ),
        },
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
    purpose: str = "audit_handoff",
    package_kind: str = DEFAULT_PACKAGE_KIND,
    boundary: dict[str, Any] | None = None,
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

    manifest = build_package_manifest(
        copied,
        policy_profile=policy_profile,
        purpose=purpose,
        package_kind=package_kind,
        boundary=boundary,
    )

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


def build_vault_aware_bundle_payload(
    profile: SayaneProfile,
    *,
    scopes: list[str] | None = None,
    profile_id: str = "default",
) -> dict[str, Any]:
    """Build one provenance-aware context bundle for external package exchange."""
    selected_scopes = scopes or list(DEFAULT_EXPORT_SCOPES)
    payload = pick_profile_sections(profile, selected_scopes)
    metadata = build_bundle_metadata(
        transfer_stage="vault_aware_external_package_export",
        transfer_path=["Sayane", "ExternalPackage"],
        profile_id=profile_id,
        system_version=__version__,
    )
    metadata["source"] = "sayane_vault_aware_package"
    metadata["uncertainty"] = "external package content is reviewable context, not canonical profile state"
    metadata["retention"] = {
        "retention_class": "reviewable_context_bundle",
        **RETENTION_CLASS_RULES["reviewable_context_bundle"],
    }
    payload["metadata"] = metadata
    content_hash = compute_bundle_hash(payload)
    payload["content_hash"] = {
        "algorithm": "sha256",
        "value": content_hash,
        "bundle_id": generate_bundle_id(content_hash),
    }
    payload["metadata"]["bundle_id"] = generate_bundle_id(content_hash)
    return payload


def write_vault_aware_bundle(
    output_path: Path,
    profile: SayaneProfile,
    *,
    scopes: list[str] | None = None,
    profile_id: str = "default",
) -> Path:
    """Write one provenance-aware context bundle for package export."""
    payload = build_vault_aware_bundle_payload(
        profile,
        scopes=scopes,
        profile_id=profile_id,
    )
    output_path.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return output_path


def build_vault_aware_package(
    output_dir: Path,
    *,
    profile: SayaneProfile,
    profile_id: str = "default",
    scopes: list[str] | None = None,
    audit_store: AuditStore | None = None,
    include_audit: bool = True,
    sign: bool = False,
    key_id: str | None = None,
) -> dict[str, Any]:
    """Create one reviewable external package from current local profile state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        staging = Path(tmpdir)
        artifacts: dict[str, Path] = {}
        bundle_path = write_vault_aware_bundle(
            staging / "bundle.yml",
            profile,
            scopes=scopes,
            profile_id=profile_id,
        )
        artifacts["bundle"] = bundle_path

        if include_audit and audit_store is not None:
            audit_path = staging / "audit-export.json"
            audit_path.write_text(
                build_export(audit_store, format="json", redact=True),
                encoding="utf-8",
            )
            artifacts["audit"] = audit_path

        manifest = create_package(
            output_dir=output_dir,
            artifacts=artifacts,
            policy_profile="vault-aware-external",
            purpose="reviewable_external_exchange",
            package_kind=VAULT_AWARE_PACKAGE_KIND,
            boundary={
                **VAULT_AWARE_BOUNDARY_DEFAULTS,
            },
            sign=sign,
            key_id=key_id,
        )
    return manifest


def locate_package_artifact(package_dir: Path, role: str) -> Path | None:
    """Locate one package artifact by manifest role."""
    manifest = inspect_package(package_dir)
    if manifest is None:
        return None
    for artifact in manifest.get("artifacts", []):
        if artifact.get("role") == role:
            return package_dir / artifact.get("path", "")
    return None


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
            "package_kind": manifest.get("package_kind") if manifest else None,
            "artifact_count": len(manifest.get("artifacts", [])) if manifest else 0,
            "signed_artifacts": manifest.get("summary", {}).get("signed_artifacts", 0) if manifest else 0,
            "unsigned_artifacts": manifest.get("summary", {}).get("unsigned_artifacts", 0) if manifest else 0,
            "invalid_artifacts": manifest.get("summary", {}).get("invalid_artifacts", 0) if manifest else 0,
            "retention": manifest.get("retention", {}) if manifest else {},
        },
        "artifacts": [],
        "scoped_contexts": [],
        "audit_summary": {"approve": 0, "reject": 0, "modify": 0, "defer": 0, "scoped_accept": 0},
        "policy": {"source": "built_in", "name": manifest.get("policy", {}).get("profile", "standard") if manifest else "unknown", "status": "UNKNOWN"},
        "boundary": manifest.get("boundary", {}) if manifest else {},
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
            "retention": art.get("retention", {}),
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
    package_retention = preview["package"].get("retention", {})
    if _is_retention_expired(
        manifest.get("created_at") if manifest else None,
        package_retention.get("recommended_max_age") if isinstance(package_retention, dict) else None,
    ):
        preview["risks"]["warnings"].append(
            {
                "code": "package_retention_expired",
                "message": "Package age exceeds the recommended review window.",
            }
        )

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
        f"  Kind: {pkg['package_kind'] or 'N/A'}",
        "",
        "Artifacts:",
    ]
    for art in preview["artifacts"]:
        lines.append(f"  - {art['role']}: {art['path']}")
        lines.append(f"    hash: {art['hash_status']}, sig: {art['signature_status']}")
        retention = art.get("retention", {})
        if retention:
            lines.append(
                "    retention: "
                f"{retention.get('retention_class', '?')} "
                f"(max_age={retention.get('recommended_max_age', '?')}, "
                f"delete_after_review={retention.get('delete_after_import_or_review', '?')})"
            )

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
    package_retention = pkg.get("retention", {})
    if package_retention:
        lines.append(
            "  retention: "
            f"{package_retention.get('package_class', '?')} "
            f"(max_age={package_retention.get('recommended_max_age', '?')})"
        )

    lines.append("")
    lines.append("Boundary:")
    boundary = preview.get("boundary", {})
    import_contract = boundary.get("import_contract")
    if import_contract:
        lines.append(
            "  import_contract: "
            f"{import_contract} "
            f"(profile_mutation_allowed={boundary.get('profile_mutation_allowed', '?')}, "
            f"candidate_persistence_allowed={boundary.get('candidate_persistence_allowed', '?')})"
        )
    retention_mode = boundary.get("retention_expiry_mode")
    if retention_mode:
        lines.append(f"  retention_expiry_mode: {retention_mode}")
    supported = boundary.get("supported_operator_actions", [])
    forbidden = boundary.get("forbidden_workflows", [])
    if supported:
        lines.append(f"  supported: {', '.join(str(item) for item in supported)}")
    if forbidden:
        lines.append(f"  forbidden: {', '.join(str(item) for item in forbidden)}")
    reserved = boundary.get("reserved_future_mutating_workflow")
    if reserved:
        lines.append(f"  reserved_future_mutating_workflow: {reserved}")

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

    lines.append("  This is a preview only. No profile has been modified.")
    lines.append("  Verified packages are not automatically accepted.")

    return "\n".join(lines)
