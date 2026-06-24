"""App-facing candidate view-model helpers."""

from __future__ import annotations

from collections import Counter
from typing import Any


def build_app_candidate_queue(items: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a UI-friendly candidate queue payload from candidate summaries."""
    statuses = Counter(str(item.get("status", "")) for item in items)
    sections = Counter(str(item.get("section", "")) for item in items if item.get("section"))
    return {
        "kind": "resident_app_candidate_queue",
        "items": items,
        "reviewable_count": len(items),
        "is_review_surface": True,
        "status_counts": dict(statuses),
        "top_sections": [
            {"section": section, "count": count} for section, count in sections.most_common(3)
        ],
    }


def build_app_candidate_detail(payload: dict[str, Any]) -> dict[str, Any]:
    """Add UI-friendly summary and action metadata to one candidate payload."""
    status = str(payload.get("status", ""))
    proposal = payload.get("proposal") or {}
    evaluation = payload.get("evaluation") or {}
    allowed_actions = {
        "evaluate": status not in {"approved", "rejected"},
        "approve": status == "evaluated",
        "reject": status not in {"approved", "rejected"},
        "revise": status not in {"approved", "rejected"},
        "show_diff": True,
    }
    payload["ui_summary"] = {
        "status": status,
        "section": proposal.get("section"),
        "operation": proposal.get("operation"),
        "source_type": (payload.get("source") or {}).get("type"),
        "evaluation_level": evaluation.get("level"),
        "rde_class": evaluation.get("rde_class"),
        "can_approve": allowed_actions["approve"],
    }
    payload["allowed_actions"] = allowed_actions
    return payload


def build_app_candidate_diff(payload: dict[str, Any]) -> dict[str, Any]:
    """Add UI-friendly diff summary metadata to one diff payload."""
    list_diff = payload.get("list_diff") or {}
    summary = {
        "section": payload.get("section"),
        "recommended_section": payload.get("recommended_section"),
        "profile_update_recommended": bool(payload.get("profile_update_recommended")),
        "has_duplicates": bool(payload.get("has_duplicates")),
        "added_count": len(payload.get("add") or []),
        "already_present_count": len(payload.get("already_present") or []),
        "removed_count": len(payload.get("remove") or []),
        "list_operation": list_diff.get("operation"),
        "list_added_count": len(list_diff.get("added") or []),
        "list_removed_count": len(list_diff.get("removed") or []),
        "list_unchanged_count": list_diff.get(
            "unchanged_count", len(list_diff.get("unchanged") or [])
        ),
        "has_structured_list_diff": bool(list_diff),
        "has_note": bool(payload.get("note")),
    }
    payload["ui_summary"] = summary
    return payload
