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

    if section == "knowledge.concepts":
        existing = set(profile.knowledge.concepts if profile.knowledge else [])
        for item in proposal.add:
            if item in existing:
                result["already_present"].append(item)
            else:
                result["add"].append(item)
        return result

    result["note"] = f"Diff for section {section} is not automated in Phase 4 MVP."
    result["proposed_add"] = proposal.add
    return result
