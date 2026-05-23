"""Rule-based diff between Profile and Candidate proposal."""

from typing import Any

from omomuki.core.candidate import CandidateUpdate
from omomuki.core.models import OmomukiProfile


def profile_diff_for_candidate(
    profile: OmomukiProfile,
    candidate: CandidateUpdate,
) -> dict[str, Any]:
    """Describe what would change if the candidate were merged."""
    proposal = candidate.proposal
    section = proposal.section
    result: dict[str, Any] = {
        "profile_id": candidate.target_profile_id,
        "candidate_id": candidate.id,
        "section": section,
        "add": [],
        "already_present": [],
    }

    existing = _existing_items(profile, section)
    if existing is None:
        result["note"] = f"Diff for section {section} is not automated."
        result["proposed_add"] = proposal.add
        return result

    for item in proposal.add:
        if item in existing:
            result["already_present"].append(item)
        else:
            result["add"].append(item)
    return result


def _existing_items(profile: OmomukiProfile, section: str) -> set[str] | None:
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
