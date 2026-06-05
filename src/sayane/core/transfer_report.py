"""Cross-LLM Transfer Regression Dashboard (Phase 10).

Generates a unified report from transfer fixtures, audit records,
and phase evaluation records. Detects regressions and produces
a PASS / PASS_WITH_WARNINGS / FAIL status.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sayane.core.audit_trail import AuditStore
from sayane.core.bundle_provenance import verify_bundle
from sayane.core.import_bundle import parse_bundle, import_bundle_with_semantic_review
from sayane.core.loader import load_profile


# --- Report generation ---


def _scan_fixtures(transfer_dir: Path) -> list[Path]:
    """Find all YAML/JSON fixtures in a transfer directory."""
    if not transfer_dir.is_dir():
        return []
    fixtures: list[Path] = []
    for ext in (".yml", ".yaml", ".json"):
        fixtures.extend(sorted(transfer_dir.glob(f"*{ext}")))
    return fixtures


def _phase_from_markdown(path: Path) -> dict[str, Any] | None:
    """Extract phase info from an evaluation record markdown."""
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    # Extract status
    import re
    status_match = re.search(r"Status:\s*(.+)", text)
    status = status_match.group(1).strip() if status_match else "unknown"
    # Extract phase name
    phase_match = re.search(r"Phase \d+:", text)
    phase = phase_match.group(0).rstrip(":") if phase_match else path.stem
    # Extract test count
    tests_match = re.search(r"phase\d+_tests:\s*(\d+)", text)
    tests = int(tests_match.group(1)) if tests_match else None

    return {"phase": phase, "status": status, "tests": tests, "record_path": str(path)}


def generate_transfer_report(
    transfer_dir: Path,
    audit_store: AuditStore,
    profile_path: Path,
) -> dict[str, Any]:
    """Generate a full transfer regression report.

    Returns a dict suitable for JSON output or markdown rendering.
    """
    now = datetime.now(UTC).isoformat()
    report: dict[str, Any] = {
        "generated_at": now,
        "status": "PASS",
        "summary": {},
        "phases": [],
        "bundles": [],
        "candidates": [],
        "audit": {},
        "regressions": {"critical": [], "warnings": []},
    }

    # Scan fixtures
    fixtures = _scan_fixtures(transfer_dir)

    # Phase records
    for md_path in sorted(transfer_dir.glob("phase*-*-evaluation-record.md")):
        phase = _phase_from_markdown(md_path)
        if phase:
            report["phases"].append(phase)

    # Bundle verification
    verified = unverified = failed = 0
    profile = None
    try:
        profile = load_profile(profile_path)
    except Exception:
        pass

    for fpath in fixtures:
        parsed = parse_bundle(fpath)
        if parsed is None:
            continue
        result = verify_bundle(parsed)
        bundle_entry: dict[str, Any] = {
            "path": str(fpath),
            "bundle_id": result.bundle_id or "unknown",
            "hash_status": result.status,
            "signature_status": result.signature_status,
            "transfer_path": [],
        }
        # Extract transfer path from metadata
        meta = parsed.get("metadata", {})
        if isinstance(meta, dict):
            transfer = meta.get("transfer", {})
            if isinstance(transfer, dict):
                bundle_entry["transfer_path"] = transfer.get("path", [])

        if result.status == "verified":
            verified += 1
        elif result.status == "failed":
            failed += 1
            report["regressions"]["critical"].append({
                "code": "bundle_hash_mismatch",
                "message": f"Bundle hash mismatch: {fpath.name}",
                "source": str(fpath),
            })
        else:
            unverified += 1
            report["regressions"]["warnings"].append({
                "code": "unverified_bundle",
                "message": f"Unverified bundle: {fpath.name}",
                "source": str(fpath),
            })

        # Candidate / warning analysis
        if profile:
            try:
                candidates, review = import_bundle_with_semantic_review(parsed, profile)
                candidate_summary = {"fixture": fpath.name, "count": len(candidates), "review_required": 0, "semantic_overlap": 0, "unstable_placement": 0, "boundary_sensitive": 0}
                for flags in review.get("candidate_flags", []):
                    if "review_required" in flags:
                        candidate_summary["review_required"] += 1
                    if "semantic_overlap" in flags:
                        candidate_summary["semantic_overlap"] += 1
                    if "unstable_placement" in flags:
                        candidate_summary["unstable_placement"] += 1
                    if "boundary_sensitive" in flags:
                        candidate_summary["boundary_sensitive"] += 1
                report["candidates"].append(candidate_summary)
            except Exception:
                pass

        report["bundles"].append(bundle_entry)

    # Audit trail
    audit_records = audit_store.read_all()
    decisions: dict[str, int] = {"approve": 0, "reject": 0, "modify": 0, "defer": 0}
    for r in audit_records:
        d_type = r.get("decision", {}).get("type", "unknown")
        if d_type in decisions:
            decisions[d_type] += 1
        # Check audit has bundle_id
        if not r.get("source", {}).get("bundle_id"):
            report["regressions"]["warnings"].append({
                "code": "audit_missing_bundle_id",
                "message": f"Audit record {r.get('id', '?')[:12]} missing bundle_id",
                "source": "audit",
            })

    report["audit"] = {"records": len(audit_records), "decisions": decisions}

    # Summary
    total_candidates = sum(c["count"] for c in report["candidates"])
    total_review_required = sum(c["review_required"] for c in report["candidates"])
    total_overlap = sum(c["semantic_overlap"] for c in report["candidates"])
    total_unstable = sum(c["unstable_placement"] for c in report["candidates"])
    total_boundary = sum(c["boundary_sensitive"] for c in report["candidates"])

    report["summary"] = {
        "fixtures": len(fixtures),
        "verified_bundles": verified,
        "unverified_bundles": unverified,
        "failed_bundles": failed,
        "candidates": total_candidates,
        "review_required": total_review_required,
        "semantic_overlap_warnings": total_overlap,
        "unstable_placement_warnings": total_unstable,
        "boundary_sensitive_warnings": total_boundary,
        "audit_records": len(audit_records),
        "critical_regressions": len(report["regressions"]["critical"]),
        "warnings": len(report["regressions"]["warnings"]),
    }

    # Regression status
    if report["summary"]["critical_regressions"] > 0:
        report["status"] = "FAIL"
    elif report["summary"]["warnings"] > 0:
        report["status"] = "PASS_WITH_WARNINGS"

    return report


# --- Markdown rendering ---

def render_markdown_report(report: dict[str, Any]) -> str:
    s = report["summary"]
    lines: list[str] = []
    lines.append("# Sayane Cross-LLM Transfer Regression Report")
    lines.append("")
    lines.append(f"Generated: {report['generated_at']}")
    lines.append("")

    # Regression status
    status = report["status"]
    emoji = {"PASS": "✅", "PASS_WITH_WARNINGS": "⚠️", "FAIL": "❌"}.get(status, "❓")
    lines.append(f"## Regression Status: {emoji} {status}")
    lines.append("")
    lines.append(f"- Critical regressions: {s['critical_regressions']}")
    lines.append(f"- Warnings: {s['warnings']}")
    lines.append("")

    # Summary
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    rows = [
        ("Transfer fixtures", s["fixtures"]),
        ("Verified bundles", s["verified_bundles"]),
        ("Unverified bundles", s["unverified_bundles"]),
        ("Failed bundles", s["failed_bundles"]),
        ("Import candidates", s["candidates"]),
        ("Review-required candidates", s["review_required"]),
        ("Semantic overlap warnings", s["semantic_overlap_warnings"]),
        ("Unstable placement warnings", s["unstable_placement_warnings"]),
        ("Boundary-sensitive warnings", s["boundary_sensitive_warnings"]),
        ("Audit records", s["audit_records"]),
    ]
    for label, val in rows:
        lines.append(f"| {label} | {val} |")
    lines.append("")

    # Phase status
    if report["phases"]:
        lines.append("## Phase Status")
        lines.append("")
        lines.append("| Phase | Status | Tests |")
        lines.append("|---|---|---|")
        for p in report["phases"]:
            lines.append(f"| {p['phase']} | {p['status']} | {p.get('tests', 'N/A')} |")
        lines.append("")

    # Bundle verification
    if report["bundles"]:
        lines.append("## Bundle Verification")
        lines.append("")
        lines.append("| Bundle | Hash Status | Signature | Transfer Path |")
        lines.append("|---|---|---|---|")
        for b in report["bundles"]:
            path = b.get("path", "").split("/")[-1]
            tp = " → ".join(b.get("transfer_path", [])) or "unknown"
            lines.append(f"| {path} | {b['hash_status']} | {b['signature_status']} | {tp} |")
        lines.append("")

    # Candidate warnings
    if report["candidates"]:
        lines.append("## Candidate / Warning Summary")
        lines.append("")
        lines.append("| Fixture | Candidates | Review Req. | Overlap | Unstable | Boundary |")
        lines.append("|---|---|---|---|---|---|")
        for c in report["candidates"]:
            lines.append(f"| {c['fixture']} | {c['count']} | {c['review_required']} | {c['semantic_overlap']} | {c['unstable_placement']} | {c['boundary_sensitive']} |")
        lines.append("")

    # Audit
    audit = report["audit"]
    lines.append("## Audit Trail Summary")
    lines.append("")
    lines.append(f"Total records: {audit['records']}")
    lines.append("")
    lines.append("| Decision | Count |")
    lines.append("|---|---|")
    for d_type, count in audit.get("decisions", {}).items():
        lines.append(f"| {d_type} | {count} |")
    lines.append("")

    # Regression details
    crit = report["regressions"]["critical"]
    warns = report["regressions"]["warnings"]
    if crit or warns:
        lines.append("## Regression Details")
        lines.append("")
        if crit:
            lines.append("### Critical")
            lines.append("")
            for r in crit:
                lines.append(f"- [{r['code']}] {r['message']}")
            lines.append("")
        if warns:
            lines.append("### Warnings")
            lines.append("")
            for w in warns:
                lines.append(f"- [{w['code']}] {w['message']}")
            lines.append("")

    return "\n".join(lines)
