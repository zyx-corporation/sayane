"""Apply approved Candidate updates to Profile (controlled sections)."""

from datetime import UTC, datetime

from omomuki.core.candidate import CandidateUpdate
from omomuki.core.models import Knowledge, OmomukiProfile, Policy, ResponsePolicy
from omomuki.evaluators.sections import BLOCKED_SECTIONS, can_merge_section

_CRITICAL_MSG = (
    "Merge to critical section '{section}' requires --force-critical on approve. "
    "Edit profile manually after review."
)


def merge_candidate_into_profile(
    profile: OmomukiProfile,
    candidate: CandidateUpdate,
    *,
    force_critical: bool = False,
) -> OmomukiProfile:
    """Merge approved candidate into allowed profile sections."""
    section = candidate.proposal.section

    if section in BLOCKED_SECTIONS:
        raise ValueError(f"Merge to '{section}' is not allowed. Edit profile manually.")

    if not can_merge_section(section, force_critical=force_critical):
        raise ValueError(_CRITICAL_MSG.format(section=section))

    if section == "knowledge.concepts":
        _merge_knowledge(profile, candidate)
    elif section == "values.core":
        _merge_values(profile, candidate)
    elif section == "voice.tone":
        _merge_tone(profile, candidate)
    elif section == "policy.response.avoid":
        _merge_policy_list(profile, candidate, field="avoid")
    elif section == "policy.response.prefer":
        _merge_policy_list(profile, candidate, field="prefer")
    elif section == "identity.roles":
        _merge_roles(profile, candidate)
    else:
        raise ValueError(f"Unsupported merge section: {section}")

    profile.lineage.updated_at = datetime.now(UTC)
    return profile


def _merge_knowledge(profile: OmomukiProfile, candidate: CandidateUpdate) -> None:
    if profile.knowledge is None:
        profile.knowledge = Knowledge(concepts=[])
    for item in candidate.proposal.add:
        if item and item not in profile.knowledge.concepts:
            profile.knowledge.concepts.append(item)


def _merge_values(profile: OmomukiProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.values.core:
            profile.values.core.append(item)


def _merge_tone(profile: OmomukiProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.voice.tone:
            profile.voice.tone.append(item)


def _merge_roles(profile: OmomukiProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.identity.roles:
            profile.identity.roles.append(item)


def _merge_policy_list(
    profile: OmomukiProfile,
    candidate: CandidateUpdate,
    *,
    field: str,
) -> None:
    if profile.policy.response is None:
        profile.policy = Policy(response=ResponsePolicy())
    response = profile.policy.response
    assert response is not None
    target: list[str] = response.avoid if field == "avoid" else response.prefer
    for item in candidate.proposal.add:
        if item and item not in target:
            target.append(item)
