"""MCP scoped context output (F-2).

Preserves scope, conditions, and negative constraints when compiled
context is sent to AI tools through MCP.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from sayane.core.review_decision import ReviewDecision


McpExposureClass = Literal[
    "global_profile",
    "project_context",
    "approved_candidate",
    "pending_candidate",
    "rejected_candidate",
    "raw_capture",
    "evaluation_metadata",
    "unknown",
]

_ALLOWED_NORMAL_CANDIDATE_DECISIONS = {"approve", "scoped_accept"}
_BLOCKED_NORMAL_CANDIDATE_DECISIONS = {"reject", "defer", "modify"}


def get_candidate_mcp_exposure_class(decision: ReviewDecision | None) -> McpExposureClass:
    """Classify how a Candidate review decision may be exposed through MCP.

    A missing decision is treated as pending. Pending/rejected/deferred/modified
    Candidate content must not be exposed through normal context endpoints.
    """
    if decision is None:
        return "pending_candidate"
    if decision.decision in _ALLOWED_NORMAL_CANDIDATE_DECISIONS:
        return "approved_candidate"
    if decision.decision in _BLOCKED_NORMAL_CANDIDATE_DECISIONS:
        return "rejected_candidate" if decision.decision == "reject" else "pending_candidate"
    return "unknown"


def can_expose_candidate_content_via_mcp(decision: ReviewDecision | None) -> bool:
    """Return True only for review-safe Candidate content.

    This is the central guard for normal MCP context endpoints. Review-only MCP
    tools may expose metadata separately, but they must not use this path as a
    bulk context provider.
    """
    return get_candidate_mcp_exposure_class(decision) == "approved_candidate"


def build_mcp_exposure_denial(
    reason: str,
    *,
    candidate_id: str | None = None,
    exposure_class: McpExposureClass = "unknown",
) -> dict[str, Any]:
    """Build a narrow fail-closed diagnostic for blocked MCP exposure."""
    payload: dict[str, Any] = {
        "ok": False,
        "error": reason,
        "exposure_class": exposure_class,
        "exposes_content": False,
    }
    if candidate_id:
        payload["candidate_id"] = candidate_id
    return payload


def _build_approved_candidate_entry(decision: ReviewDecision, mode: str) -> dict[str, Any]:
    """Render an approved Candidate as MCP-safe context with metadata."""
    entry: dict[str, Any] = {
        "candidate_id": decision.candidate_id,
        "decision": decision.decision,
        "section": decision.original_section,
        "source_action": decision.original_action,
        "lineage_event_id": decision.lineage_event_id,
        "decided_at": decision.decided_at,
        "exposure_class": "approved_candidate",
    }

    if decision.decision == "scoped_accept":
        entry["accepted_scope"] = decision.accepted_scope

    if mode != "compact":
        entry["content"] = decision.applied_value
        entry["reason"] = decision.reason
        if decision.original_proposed is not None:
            entry["original_proposed"] = decision.original_proposed

    if mode == "full":
        entry["review_flags"] = decision.review_flags
        entry["review_warnings"] = decision.review_warnings
        entry["overlap_groups"] = decision.overlap_groups

    return entry


def filter_mcp_exposable_candidates(
    decisions: list[ReviewDecision | None],
) -> tuple[list[ReviewDecision], list[dict[str, Any]]]:
    """Split Candidate decisions into exposable decisions and fail-closed denials."""
    exposable: list[ReviewDecision] = []
    denials: list[dict[str, Any]] = []

    for decision in decisions:
        exposure_class = get_candidate_mcp_exposure_class(decision)
        candidate_id = decision.candidate_id if decision else None
        if exposure_class == "approved_candidate" and decision is not None:
            exposable.append(decision)
            continue
        denials.append(
            build_mcp_exposure_denial(
                "candidate_not_approved",
                candidate_id=candidate_id,
                exposure_class=exposure_class,
            )
        )

    return exposable, denials


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
        "included_approved_candidates": [],
        "blocked_candidates": [],
        "warnings": [],
    }

    exposable_decisions, denials = filter_mcp_exposable_candidates(scoped)
    output["blocked_candidates"].extend(denials)

    for d in exposable_decisions:
        if d.decision == "approve":
            output["included_approved_candidates"].append(
                _build_approved_candidate_entry(d, mode)
            )
            continue

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
        output["included_approved_candidates"].append(
            _build_approved_candidate_entry(d, mode)
        )

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

    blocked = compiled.get("blocked_candidates", [])
    if blocked:
        lines.append("## Blocked Candidate Context")
        lines.append("")
        for denial in blocked:
            cid = denial.get("candidate_id", "N/A")
            reason = denial.get("error", "blocked")
            lines.append(f"- {cid}: {reason}")
        lines.append("")

    for w in compiled.get("warnings", []):
        lines.append(f"> {w}")

    return "\n".join(lines)
