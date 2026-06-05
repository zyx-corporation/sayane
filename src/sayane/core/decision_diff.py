"""Review Decision Diff Viewer (Phase 13).

Renders human-readable diffs from review decisions and audit records.
Shows what was preserved, transformed, removed, added, or deferred.
Semantic hints are hint_only — no auto-judgement.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


# --- Diff model ---

@dataclass
class DecisionDiff:
    candidate_id: str
    decision: str  # approve | reject | modify | defer
    section: str
    original_candidate: Any
    applied_value: Any
    preserved: list[str] = field(default_factory=list)
    transformed: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    unresolved: list[str] = field(default_factory=list)
    semantic_hints: list[str] = field(default_factory=list)
    rde_classification: list[str] = field(default_factory=list)
    status: str = ""  # applied_as_proposed | not_applied | applied_with_modification | pending
    warnings: list[dict[str, Any]] = field(default_factory=list)


# --- Structural diff helpers ---

def _describe_value(v: Any) -> str:
    if v is None:
        return "<none>"
    import json
    return json.dumps(v, ensure_ascii=False)[:120]


def compute_structural_diff(original: Any, applied: Any) -> dict[str, list[str]]:
    """Compute a simple structural diff between original and applied values."""
    result: dict[str, list[str]] = {"preserved": [], "transformed": [], "removed": [], "added": []}

    if applied is None and original is not None:
        result["removed"].append(f"Value not applied: {_describe_value(original)}")
        return result

    if original is None and applied is not None:
        result["added"].append(f"New value: {_describe_value(applied)}")
        return result

    if original == applied:
        result["preserved"].append("Value applied as-is.")
        return result

    # Different types → transformation
    if type(original) != type(applied):
        result["transformed"].append(f"Value transformed: {_describe_value(original)} → {_describe_value(applied)}")
        return result

    # Dict diff
    if isinstance(original, dict) and isinstance(applied, dict):
        for k in set(original.keys()) | set(applied.keys()):
            ov = original.get(k)
            av = applied.get(k)
            if k not in applied:
                result["removed"].append(f"Key '{k}' removed: {_describe_value(ov)}")
            elif k not in original:
                result["added"].append(f"Key '{k}' added: {_describe_value(av)}")
            elif ov != av:
                result["transformed"].append(f"Key '{k}': {_describe_value(ov)} → {_describe_value(av)}")
        return result

    # List diff
    if isinstance(original, list) and isinstance(applied, list):
        orig_set = {str(v).strip().lower() if isinstance(v, str) else str(v) for v in original}
        appl_set = {str(v).strip().lower() if isinstance(v, str) else str(v) for v in applied}
        preserved = orig_set & appl_set
        removed_items = orig_set - appl_set
        added_items = appl_set - orig_set
        for p in preserved:
            result["preserved"].append(f"'{p}' retained.")
        for r in removed_items:
            result["removed"].append(f"'{r}' not applied.")
        for a in added_items:
            result["added"].append(f"'{a}' added.")
        return result

    # Scalar diff
    result["transformed"].append(f"{_describe_value(original)} → {_describe_value(applied)}")
    return result


# --- Semantic hints ---

SEMANTIC_HINTS: dict[str, dict[str, str]] = {
    ("sayane", "sayane"): {
        "standalone_principle": "context_portability_principle",
        "hint": "Sayane was narrowed from a standalone term into a context-portability formulation.",
    },
    ("rde", "rde"): {
        "same_term": "same_term",
        "hint": "RDE was retained without semantic change.",
    },
}


def compute_semantic_hints(original: Any, applied: Any) -> list[str]:
    """Generate hint-only semantic observations. Never auto-judges."""
    hints: list[str] = []

    def _collect_terms(v: Any) -> set[str]:
        if isinstance(v, str):
            return {v.strip().lower()}
        if isinstance(v, list):
            return {str(x).strip().lower() for x in v if isinstance(x, str)}
        if isinstance(v, dict):
            result: set[str] = set()
            for val in v.values():
                result.update(_collect_terms(val))
            return result
        return set()

    orig_terms = _collect_terms(original)
    appl_terms = _collect_terms(applied)

    for key, hint in SEMANTIC_HINTS.items():
        t1, t2 = key
        if t1 in orig_terms and t2 in appl_terms:
            hints.append(hint["hint"])

    return hints


# --- Decision diff builder ---

def build_decision_diff(
    candidate_id: str,
    decision: str,
    section: str,
    original_candidate: Any,
    applied_value: Any,
    reason: str = "",
    warnings_in: list[dict[str, Any]] | None = None,
) -> DecisionDiff:
    """Build a DecisionDiff from a review decision."""
    warnings = warnings_in or []
    structural = compute_structural_diff(original_candidate, applied_value)
    hints = compute_semantic_hints(original_candidate, applied_value)

    # Determine status
    if decision == "approve":
        status = "applied_as_proposed"
        rde = ["preserved"]
    elif decision == "reject":
        status = "not_applied"
        structural["preserved"].append("Original candidate was preserved in audit trail.")
        rde = ["rejected"]
    elif decision == "modify":
        status = "applied_with_modification"
        rde = ["preserved", "authorized_transformation"]
    else:  # defer
        status = "pending"
        structural["unresolved"] = ["Decision deferred for later review."]
        rde = ["deferred"]

    return DecisionDiff(
        candidate_id=candidate_id,
        decision=decision,
        section=section,
        original_candidate=original_candidate,
        applied_value=applied_value,
        preserved=structural["preserved"],
        transformed=structural["transformed"],
        removed=structural["removed"],
        added=structural["added"],
        unresolved=structural.get("unresolved", []),
        semantic_hints=hints,
        rde_classification=rde,
        status=status,
        warnings=warnings,
    )


# --- Diff renderer ---

def render_diff(diff: DecisionDiff) -> str:
    """Render a decision diff as human-readable text."""
    import json
    lines: list[str] = []
    lines.append(f"=== Review Decision Diff: {diff.candidate_id} ===")
    lines.append("")
    lines.append(f"Decision: {diff.decision.upper()}")
    lines.append(f"Section: {diff.section}")
    lines.append(f"Status: {diff.status}")
    lines.append("")

    lines.append("Original candidate:")
    lines.append(f"  {json.dumps(diff.original_candidate, ensure_ascii=False)}")
    lines.append("")

    lines.append("Applied value:")
    lines.append(f"  {json.dumps(diff.applied_value, ensure_ascii=False) if diff.applied_value else '<none>'}")
    lines.append("")

    lines.append("Diff summary:")
    for category, items in [
        ("Preserved", diff.preserved),
        ("Transformed", diff.transformed),
        ("Removed", diff.removed),
        ("Added", diff.added),
        ("Unresolved", diff.unresolved),
    ]:
        for item in items:
            lines.append(f"  {category}: {item}")
    lines.append("")

    if diff.semantic_hints:
        lines.append("Semantic hints:")
        for h in diff.semantic_hints:
            lines.append(f"  - {h}")
        lines.append("")

    if diff.warnings:
        lines.append("Warnings at decision time:")
        for w in diff.warnings:
            lines.append(f"  - {w.get('message', w)}")
        lines.append("")

    lines.append(f"RDE: {', '.join(diff.rde_classification)}")
    lines.append("")

    return "\n".join(lines)


# --- Audit diff integration ---

def diff_from_audit_record(record: dict[str, Any]) -> DecisionDiff:
    """Build a DecisionDiff from a Phase 8 audit record."""
    decision = record.get("decision", {})
    candidate = record.get("candidate", {})
    diff_data = record.get("diff", {})

    return DecisionDiff(
        candidate_id=candidate.get("id", "unknown"),
        decision=decision.get("type", "unknown"),
        section=candidate.get("section", "unknown"),
        original_candidate=diff_data.get("original_candidate") or candidate.get("proposed"),
        applied_value=diff_data.get("applied_value") or decision.get("applied_value"),
        preserved=[diff_data.get("delta_summary", "")] if diff_data.get("delta_summary") else [],
        warnings=candidate.get("warnings", []),
        rde_classification=record.get("rde", {}).get("classification", []),
        status="not_applied" if decision.get("type") == "reject" else "applied_with_modification" if decision.get("type") == "modify" else "applied_as_proposed",
    )
