"""Review Decision Audit Trail (Phase 8).

Append-only audit store for candidate review decisions.
Every decision is recorded before any profile update.
Rejected/deferred candidates are preserved, not lost.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.core.review_decision import ReviewDecision


# --- Audit record schema ---

def build_audit_record(decision: ReviewDecision, profile_updated: bool = False) -> dict[str, Any]:
    """Build an audit record from a review decision."""
    original = decision.original_proposed
    applied = decision.applied_value

    delta_parts: list[str] = []
    if decision.decision == "reject":
        delta_parts.append(f"Candidate rejected: {decision.reason[:120]}")
    elif decision.decision == "modify":
        delta_parts.append(f"Modified: original={json.dumps(original, ensure_ascii=False)[:100]} → applied={json.dumps(applied, ensure_ascii=False)[:100]}")
    elif decision.decision == "defer":
        delta_parts.append("Decision deferred; no profile change.")
    elif decision.decision == "approve":
        delta_parts.append(f"Approved as-is: {json.dumps(original, ensure_ascii=False)[:100]}")

    return {
        "id": decision.lineage_event_id,
        "event_type": "review_decision",
        "created_at": decision.decided_at,
        "actor": {
            "type": "local_user",
            "id": decision.reviewer,
        },
        "source": {
            "bundle_id": getattr(decision, "bundle_id", None),
            "source_model": getattr(decision, "source_model", None),
            "transfer_path": decision.transfer_path,
        },
        "candidate": {
            "id": decision.candidate_id,
            "section": decision.original_section,
            "action": decision.original_action,
            "proposed": original,
            "flags": decision.review_flags,
            "warnings": decision.review_warnings,
        },
        "decision": {
            "type": decision.decision,
            "reason": decision.reason,
            "decided_at": decision.decided_at,
        },
        "result": {
            "profile_updated": profile_updated,
            "applied_value": applied,
            "target_path": decision.original_section if profile_updated else None,
        },
        "diff": {
            "original_candidate": original,
            "applied_value": applied,
            "delta_summary": " | ".join(delta_parts) if delta_parts else "no change",
        },
        "rde": {
            "classification": ["audit_record"],
            "note": "Review decision recorded; see decision.reason for human rationale.",
        },
    }


# --- Append-only audit store ---

class AuditStore:
    """Append-only JSONL audit store."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self._file = base_dir / "review-decisions.jsonl"

    @property
    def path(self) -> Path:
        return self._file

    def ensure_dir(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def append(self, record: dict[str, Any]) -> None:
        """Append an audit record. Never modifies existing records."""
        self.ensure_dir()
        with open(self._file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def read_all(self) -> list[dict[str, Any]]:
        """Read all audit records."""
        if not self._file.exists():
            return []
        records: list[dict[str, Any]] = []
        with open(self._file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        records.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return records

    def query(self, **filters: Any) -> list[dict[str, Any]]:
        """Simple filter-based query over audit records."""
        records = self.read_all()
        result = records
        for key, value in filters.items():
            if key == "candidate_id":
                result = [r for r in result if r.get("candidate", {}).get("id") == value]
            elif key == "decision_type":
                result = [r for r in result if r.get("decision", {}).get("type") == value]
            elif key == "section":
                result = [r for r in result if r.get("candidate", {}).get("section") == value]
            elif key == "term":
                result = [r for r in result if _audit_record_contains_term(r, value)]
            elif key == "bundle_id":
                result = [r for r in result if r.get("source", {}).get("bundle_id") == value]
        return result


def _audit_record_contains_term(record: dict[str, Any], term: str) -> bool:
    """Check if an audit record references a specific term."""
    term_lower = term.lower()
    # Check candidate proposed value
    proposed = record.get("candidate", {}).get("proposed")
    if proposed:
        proposed_str = json.dumps(proposed).lower()
        if term_lower in proposed_str:
            return True
    # Check warnings
    for w in record.get("candidate", {}).get("warnings", []):
        if term_lower in w.get("term", "").lower():
            return True
    return False


# --- Default audit store ---

_default_audit_dir = Path.home() / ".sayane" / "audit"


def get_audit_store(base_dir: Path | None = None) -> AuditStore:
    return AuditStore(base_dir or _default_audit_dir)
