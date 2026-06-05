"""Audit Trail Export (Phase 14).

Exports audit records to Markdown, JSON, or JSONL formats.
Supports filtering by candidate, term, decision, bundle, date range.
Includes optional redaction of local paths.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.core.audit_trail import AuditStore, _audit_record_contains_term
from sayane.core.decision_diff import diff_from_audit_record, render_diff


# --- Export record normalization ---

def _normalize_record(record: dict[str, Any], redact: bool = False) -> dict[str, Any]:
    """Normalize an audit record for export."""
    normalized = dict(record)  # shallow copy
    if redact:
        # Redact local paths
        source = normalized.get("source", {})
        if isinstance(source, dict):
            for key in list(source.keys()):
                if "path" in key.lower():
                    source[key] = "<redacted:path>"
        normalized["source"] = source
    return normalized


def _filter_records(
    records: list[dict[str, Any]],
    candidate_id: str | None = None,
    term: str | None = None,
    decision: str | None = None,
    bundle_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
) -> list[dict[str, Any]]:
    """Filter audit records by criteria."""
    result = records
    if candidate_id:
        result = [r for r in result if r.get("candidate", {}).get("id") == candidate_id]
    if term:
        result = [r for r in result if _audit_record_contains_term(r, term)]
    if decision:
        result = [r for r in result if r.get("decision", {}).get("type") == decision]
    if bundle_id:
        result = [r for r in result if r.get("source", {}).get("bundle_id") == bundle_id]
    if since:
        result = [r for r in result if r.get("created_at", "") >= since]
    if until:
        result = [r for r in result if r.get("created_at", "") <= until]
    return result


# --- Export builders ---

def build_export(
    store: AuditStore,
    format: str = "markdown",
    candidate_id: str | None = None,
    term: str | None = None,
    decision: str | None = None,
    bundle_id: str | None = None,
    since: str | None = None,
    until: str | None = None,
    redact: bool = False,
) -> str:
    """Build an export of audit records."""
    all_records = store.read_all()
    records = _filter_records(all_records, candidate_id, term, decision, bundle_id, since, until)
    now = datetime.now(UTC).isoformat()

    if format == "json":
        export = _build_json_export(records, now, redact, candidate_id, term, decision, bundle_id, since, until)
        return json.dumps(export, ensure_ascii=False, indent=2)

    if format == "jsonl":
        lines = []
        for r in records:
            lines.append(json.dumps(_normalize_record(r, redact), ensure_ascii=False))
        return "\n".join(lines) + "\n" if lines else ""

    # Markdown
    return _build_markdown_export(records, now, redact, candidate_id, term, decision)


def _build_json_export(
    records: list[dict[str, Any]],
    now: str,
    redact: bool,
    candidate_id: str | None,
    term: str | None,
    decision: str | None,
    bundle_id: str | None,
    since: str | None,
    until: str | None,
) -> dict[str, Any]:
    decision_counts: dict[str, int] = {"approve": 0, "reject": 0, "modify": 0, "defer": 0}
    for r in records:
        d = r.get("decision", {}).get("type", "")
        if d in decision_counts:
            decision_counts[d] += 1

    return {
        "schema_version": "audit-export-v1",
        "export_id": uuid4().hex,
        "exported_at": now,
        "filters": {
            "candidate_id": candidate_id,
            "term": term,
            "decision": decision,
            "bundle_id": bundle_id,
            "since": since,
            "until": until,
        },
        "redaction": redact,
        "summary": {
            "records": len(records),
            "decisions": decision_counts,
        },
        "records": [_normalize_record(r, redact) for r in records],
    }


def _build_markdown_export(
    records: list[dict[str, Any]],
    now: str,
    redact: bool,
    candidate_id: str | None,
    term: str | None,
    decision: str | None,
) -> str:
    lines: list[str] = []
    lines.append("# Sayane Audit Trail Export")
    lines.append("")
    lines.append(f"Exported: {now}")
    lines.append(f"Records: {len(records)}")
    lines.append(f"Redacted: {redact}")
    if candidate_id:
        lines.append(f"Filter: candidate={candidate_id}")
    if term:
        lines.append(f"Filter: term={term}")
    if decision:
        lines.append(f"Filter: decision={decision}")
    lines.append("")

    # Summary
    decision_counts: dict[str, int] = {"approve": 0, "reject": 0, "modify": 0, "defer": 0}
    for r in records:
        d = r.get("decision", {}).get("type", "")
        if d in decision_counts:
            decision_counts[d] += 1

    lines.append("## Summary")
    lines.append("")
    lines.append("| Decision | Count |")
    lines.append("|---|---|")
    for d_type, count in decision_counts.items():
        lines.append(f"| {d_type} | {count} |")
    lines.append("")

    if not records:
        lines.append("No audit records matched the given filters.")
        lines.append("")
        return "\n".join(lines)

    # Records
    lines.append("## Records")
    lines.append("")

    for i, r in enumerate(records):
        normalized = _normalize_record(r, redact)
        record_id = normalized.get("id", "?")[:12]
        cand = normalized.get("candidate", {})
        dec = normalized.get("decision", {})
        diff_data = normalized.get("diff", {})

        lines.append(f"### Record {record_id}")
        lines.append("")
        lines.append(f"- Candidate: {cand.get('id', '?')}")
        lines.append(f"- Decision: **{dec.get('type', '?').upper()}**")
        lines.append(f"- Section: {cand.get('section', '?')}")
        lines.append(f"- Reason: {dec.get('reason', 'N/A')}")
        lines.append("")

        # Original / applied
        original = diff_data.get("original_candidate") or cand.get("proposed")
        applied = diff_data.get("applied_value") or dec.get("applied_value")
        lines.append("Original candidate:")
        lines.append("```yaml")
        lines.append(json.dumps(original, ensure_ascii=False))
        lines.append("```")
        lines.append("")
        lines.append("Applied value:")
        lines.append("```yaml")
        lines.append(json.dumps(applied, ensure_ascii=False) if applied else "<none>")
        lines.append("```")
        lines.append("")

        # Diff
        delta = diff_data.get("delta_summary", "")
        if delta:
            lines.append(f"Diff: {delta}")
            lines.append("")

        # Provenance
        source = normalized.get("source", {})
        transfer = source.get("transfer_path", [])
        if transfer:
            lines.append(f"Transfer path: {' → '.join(transfer)}")
            lines.append("")

        # Warnings
        warnings = cand.get("warnings", [])
        if warnings:
            lines.append("Warnings:")
            for w in warnings:
                lines.append(f"- {w.get('message', w.get('term', str(w)))}")
            lines.append("")

    return "\n".join(lines)
