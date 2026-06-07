"""MCP scoped context output (F-2).

Preserves scope, conditions, and negative constraints when compiled
context is sent to AI tools through MCP.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sayane.core.review_decision import ReviewDecision


def build_compiled_context(
    profile_id: str = "default",
    target: str = "cursor",
    mode: str = "full",
    *,
    scoped_decisions: list[ReviewDecision] | None = None,
    include_warnings: bool = True,
) -> dict[str, Any]:
    """Build compiled context for MCP clients, preserving scoped accept metadata.

    Modes:
    - compact: minimal scope note, global instruction not implied
    - full: scope/conditions/constraints/promotion/reuse all included
    - strict: out-of-scope context omitted entirely
    """
    scoped = scoped_decisions or []

    output: dict[str, Any] = {
        "profile_id": profile_id,
        "target": target,
        "mode": mode,
        "generated_at": datetime.now(UTC).isoformat(),
        "is_derived_context": True,
        "is_canonical_profile": False,
        "included_scoped_contexts": [],
        "warnings": [],
    }

    for d in scoped:
        if d.decision != "scoped_accept":
            continue

        if mode == "strict" and d.accepted_scope:
            continue  # omit if out of scope in strict mode

        entry: dict[str, Any] = {
            "candidate_id": d.candidate_id,
            "accepted_scope": d.accepted_scope,
        }

        if mode == "full":
            entry["conditions"] = d.conditions
            entry["negative_constraints"] = d.negative_constraints
            entry["promotion_policy"] = d.promotion_policy or {"can_promote": False}
            entry["reuse_policy"] = d.reuse_policy or {"review_on_reuse": True}
        elif mode == "compact":
            if d.conditions:
                entry["conditions_summary"] = d.conditions[0][:80]
            if d.negative_constraints:
                entry["key_constraint"] = d.negative_constraints[0][:80]
            entry["review_on_reuse"] = (d.reuse_policy or {}).get("review_on_reuse", True)

        output["included_scoped_contexts"].append(entry)

    if include_warnings:
        output["warnings"].append(
            "This context is derived from Sayane profile and review records. "
            "It is not the canonical profile. Scoped context must not be reused "
            "outside its declared scope without review."
        )

    return output


def render_compiled_context_text(compiled: dict[str, Any]) -> str:
    """Render compiled context as human-readable text for display."""
    lines: list[str] = []
    lines.append(f"# Compiled Context for {compiled['target']}")
    lines.append("")
    lines.append(
        "**This is a derived context, not the canonical profile.**"
    )
    lines.append(f"Mode: {compiled['mode']}")
    lines.append("")

    for entry in compiled.get("included_scoped_contexts", []):
        scope = entry.get("accepted_scope", {})
        lines.append("## Scoped Context")
        lines.append("")
        lines.append(f"- Scope: {scope.get('target', 'N/A')} / {scope.get('sub_scope', 'N/A')}")
        lines.append(f"- Level: {scope.get('level', 'N/A')}")

        if "conditions" in entry:
            lines.append("")
            lines.append("### Conditions")
            for c in entry["conditions"]:
                lines.append(f"- {c}")

        if "negative_constraints" in entry:
            lines.append("")
            lines.append("### Must NOT be treated as")
            for nc in entry["negative_constraints"]:
                lines.append(f"- {nc}")

        if "conditions_summary" in entry:
            lines.append(f"- Condition: {entry['conditions_summary']}")
        if "key_constraint" in entry:
            lines.append(f"- Constraint: {entry['key_constraint']}")

        lines.append("")

    for w in compiled.get("warnings", []):
        lines.append(f"> {w}")

    return "\n".join(lines)
