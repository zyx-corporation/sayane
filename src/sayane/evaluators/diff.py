"""Rule-based diff between Profile and Candidate proposal."""

from typing import Any

from sayane.core.candidate import CandidateEvaluation, CandidateProposal, CandidateUpdate
from sayane.core.models import SayaneProfile
from sayane.evaluators.rde_summary import build_rde_summary_message

_REVIEW_REQUIRED = "review_required"
_MIXED_SECTIONS = "mixed_sections"


def profile_diff_for_candidate(
    profile: SayaneProfile,
    candidate: CandidateUpdate,
) -> dict[str, Any]:
    """Describe what would change if the candidate were merged."""
    proposal = candidate.proposal
    section = proposal.section
    result: dict[str, Any] = {
        "profile_id": candidate.target_profile_id,
        "candidate_id": candidate.id,
        "section": section,
        "recommended_section": _recommended_section(section, proposal.items),
        "add": [],
        "already_present": list(proposal.already_present),
        "has_duplicates": bool(proposal.already_present),
        "profile_update_recommended": False,
        "rde_summary_message": "",
    }

    if section == _REVIEW_REQUIRED or proposal.operation in (
        "parse_failed",
        "parse_failed_or_no_effective_update",
    ):
        result["recommended_section"] = _REVIEW_REQUIRED
        result["add"] = []
        result["has_duplicates"] = bool(proposal.already_present)
        if proposal.parse_error:
            result["parse_error"] = proposal.parse_error
        result["profile_update_recommended"] = False
        result["rde_summary_message"] = build_rde_summary_message(candidate, result)
        return result

    if section == _MIXED_SECTIONS:
        result["recommended_section"] = _REVIEW_REQUIRED
        result["add"] = [
            item for item in proposal.items if item.get("section")
        ]
        result["has_duplicates"] = bool(proposal.already_present)
        result["profile_update_recommended"] = _profile_update_recommended(
            section,
            proposal,
            candidate.evaluation,
            candidate.capture_meta.model_dump() if candidate.capture_meta else None,
            has_add=bool(result["add"]),
        )
        result["rde_summary_message"] = build_rde_summary_message(candidate, result)
        return result

    if section == "major_projects":
        existing_projects = _existing_projects(profile)
        add, already = _split_major_project_diff(
            proposal.items,
            existing_projects,
        )
        result["add"] = add
        result["already_present"] = _merge_already_present(
            already,
            proposal.already_present,
        )
        result["has_duplicates"] = bool(result["already_present"])
        result["recommended_section"] = _recommended_section(section, proposal.items)
        if result["recommended_section"] != section:
            result["has_duplicates"] = True
        result["profile_update_recommended"] = _profile_update_recommended(
            section,
            proposal,
            candidate.evaluation,
            candidate.capture_meta.model_dump() if candidate.capture_meta else None,
            has_add=bool(result["add"]),
        )
        result["rde_summary_message"] = build_rde_summary_message(candidate, result)
        return result

    if section == "communication_mode":
        existing = _existing_communication_items(profile)
        add, already = _split_communication_diff(proposal.items, existing)
        result["add"] = add
        result["already_present"] = _merge_already_present(
            already,
            proposal.already_present,
        )
        result["has_duplicates"] = bool(result["already_present"])
        result["profile_update_recommended"] = False
        result["rde_summary_message"] = build_rde_summary_message(candidate, result)
        return result

    existing = _existing_items(profile, section)
    if existing is None:
        result["note"] = f"Diff for section {section} is not automated."
        result["proposed_add"] = proposal.add
        result["profile_update_recommended"] = _profile_update_recommended(
            section,
            proposal,
            candidate.evaluation,
            candidate.capture_meta.model_dump() if candidate.capture_meta else None,
            has_add=bool(proposal.add),
        )
        result["rde_summary_message"] = build_rde_summary_message(candidate, result)
        return result

    for item in proposal.add:
        if item in existing:
            result["already_present"].append({"name": item, "path": section})
        else:
            result["add"].append(item)
    result["has_duplicates"] = bool(result["already_present"])
    result["profile_update_recommended"] = _profile_update_recommended(
        section,
        proposal,
        candidate.evaluation,
        candidate.capture_meta.model_dump() if candidate.capture_meta else None,
        has_add=bool(result["add"]),
    )
    result["rde_summary_message"] = build_rde_summary_message(candidate, result)
    return result


def _merge_already_present(
    primary: list[dict[str, str]],
    extra: list[dict[str, str]],
) -> list[dict[str, str]]:
    seen: set[str] = set()
    out: list[dict[str, str]] = []
    for entry in primary + extra:
        key = f"{entry.get('path', '')}:{entry.get('name', '')}:{entry.get('value', '')}"
        if key in seen:
            continue
        seen.add(key)
        out.append(entry)
    return out


def _profile_update_recommended(
    section: str,
    proposal: CandidateProposal,
    evaluation: CandidateEvaluation | None,
    capture_meta: dict[str, Any] | None,
    *,
    has_add: bool,
) -> bool:
    if section in (_MIXED_SECTIONS, "communication_mode"):
        return False
    if capture_meta:
        if capture_meta.get("capture_confidence") == "low":
            return False
        if capture_meta.get("requires_review"):
            return False
    if evaluation is not None:
        rde = evaluation.rde_class
        if rde in (
            "Preserved",
            "Unresolved Gap",
            "Suspicious Drift",
            "Critical Distortion",
        ):
            return False
        if rde == "Authorized Transformation":
            return has_add or bool(proposal.items)
        if rde == "Inferred Extension":
            return has_add and section == "major_projects"
    if section == "knowledge.concepts" and _is_communication_items(proposal.items):
        return False
    if section == "knowledge.concepts" and proposal.items:
        return False
    if proposal.operation == "no_op_or_duplicate":
        return False
    return has_add or bool(proposal.items)


def _existing_projects(profile: SayaneProfile) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in profile.major_projects:
        out[item.name.strip().lower()] = _normalize_summary(item.summary)
    return out


def _normalize_summary(summary: str | None) -> str:
    if not summary:
        return ""
    return " ".join(summary.strip().lower().split())


def _split_major_project_diff(
    items: list[dict[str, str]],
    existing: dict[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    add: list[dict[str, str]] = []
    already: list[dict[str, str]] = []
    for item in items:
        name = item.get("name", "").strip()
        if not name:
            continue
        key = name.lower()
        if key not in existing:
            add.append(item)
            continue
        if existing[key] == _normalize_summary(
            item.get("summary"),
        ):
            already.append({"path": "major_projects[].name", "name": name})
        else:
            add.append(item)
    return add, already


def _existing_items(profile: SayaneProfile, section: str) -> set[str] | None:
    if section == "knowledge.concepts":
        return set(profile.knowledge.concepts if profile.knowledge else [])
    if section == "values.core":
        return set(profile.values.core)
    if section == "voice.tone":
        return set(profile.voice.tone)
    if section == "identity.roles":
        return set(profile.identity.roles)
    if section == "policy.response.avoid":
        return set(profile.policy.response.avoid if profile.policy.response else [])
    if section == "policy.response.prefer":
        return set(profile.policy.response.prefer if profile.policy.response else [])
    return None


def _recommended_section(section: str, items: list[dict[str, str]]) -> str:
    if section == _REVIEW_REQUIRED:
        return _REVIEW_REQUIRED
    if section == _MIXED_SECTIONS:
        return _REVIEW_REQUIRED
    if section == "major_projects" and items:
        item_sections = {
            (item.get("section") or "").strip()
            for item in items
            if (item.get("section") or "").strip()
        }
        if len(item_sections) > 1:
            return _REVIEW_REQUIRED
        if item_sections - {"major_projects"}:
            return _REVIEW_REQUIRED
    if section == "knowledge.concepts" and _is_communication_items(items):
        return "communication_mode"
    if section == "knowledge.concepts" and items:
        return "major_projects"
    if section == "major_projects" and items:
        for item in items:
            name = (item.get("name") or "").strip()
            if not name:
                continue
            item_section = (item.get("section") or "").strip()
            if item_section and item_section not in ("major_projects", ""):
                return _REVIEW_REQUIRED
    return section


def _is_communication_items(items: list[dict[str, str]]) -> bool:
    if not items:
        return False
    return all(item.get("path", "").startswith("communication_mode.") for item in items)


def _existing_communication_items(profile: SayaneProfile) -> set[tuple[str, str]]:
    mode = profile.communication_mode
    if mode is None:
        return set()
    out: set[tuple[str, str]] = set()
    if mode.assistant_name_for_chatgpt:
        out.add(
            (
                "communication_mode.assistant_name_for_chatgpt",
                mode.assistant_name_for_chatgpt.strip(),
            ),
        )
    if mode.preferred_address:
        out.add(("communication_mode.preferred_address", mode.preferred_address.strip()))
    if mode.intimate_address:
        out.add(("communication_mode.intimate_address", mode.intimate_address.strip()))
    for value in mode.collaboration_style:
        out.add(("communication_mode.collaboration_style", value.strip()))
    return out


def _split_communication_diff(
    items: list[dict[str, str]],
    existing: set[tuple[str, str]],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    add: list[dict[str, str]] = []
    already: list[dict[str, str]] = []
    for item in items:
        path = item.get("path", "").strip()
        value = item.get("value", "").strip()
        if not path or not value:
            continue
        normalized = {"path": path, "value": value}
        if (path, value) in existing:
            already.append(normalized)
        else:
            add.append(normalized)
    return add, already
