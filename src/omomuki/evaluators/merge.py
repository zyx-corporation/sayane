"""Apply approved Candidate updates to Profile (controlled sections only)."""

from datetime import UTC, datetime

from omomuki.core.candidate import CandidateUpdate
from omomuki.core.models import Knowledge, OmomukiProfile

_CRITICAL_SECTIONS = frozenset({"identity", "values", "policy", "voice"})


def merge_candidate_into_profile(
    profile: OmomukiProfile,
    candidate: CandidateUpdate,
) -> OmomukiProfile:
    """Merge approved candidate. MVP: knowledge.concepts only."""
    section = candidate.proposal.section
    root = section.split(".")[0]

    if root in _CRITICAL_SECTIONS:
        msg = (
            f"Merge to critical section '{section}' is not allowed in Phase 4 MVP. "
            "Edit profile manually after review."
        )
        raise ValueError(msg)

    if section == "knowledge.concepts":
        if profile.knowledge is None:
            profile.knowledge = Knowledge(concepts=[])
        for item in candidate.proposal.add:
            if item and item not in profile.knowledge.concepts:
                profile.knowledge.concepts.append(item)
    else:
        raise ValueError(f"Unsupported merge section: {section}")

    profile.lineage.updated_at = datetime.now(UTC)
    return profile
