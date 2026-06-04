"""Apply approved Candidate updates to Profile (controlled sections)."""

from datetime import UTC, datetime

from sayane.core.candidate import CandidateUpdate
from sayane.core.models import (
    CommunicationMode,
    Knowledge,
    MajorProject,
    Policy,
    ResponsePolicy,
    SayaneProfile,
)
from sayane.evaluators.sections import BLOCKED_SECTIONS, can_merge_section

_CRITICAL_MSG = (
    "Merge to critical section '{section}' requires --force-critical "
    "on approve. Edit profile manually after review."
)


def merge_candidate_into_profile(
    profile: SayaneProfile,
    candidate: CandidateUpdate,
    *,
    force_critical: bool = False,
) -> SayaneProfile:
    """Merge approved candidate into allowed profile sections."""
    section = candidate.proposal.section

    if section in BLOCKED_SECTIONS:
        raise ValueError(
            f"Merge to '{section}' is not allowed. Edit profile manually.",
        )

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
    elif section == "major_projects":
        _merge_major_projects(profile, candidate)
    elif section == "communication_mode":
        _merge_communication_mode(profile, candidate)
    elif section == "important_terms":
        _merge_important_terms(profile, candidate)
    else:
        raise ValueError(f"Unsupported merge section: {section}")

    profile.lineage.updated_at = datetime.now(UTC)
    return profile


def _merge_important_terms(profile: SayaneProfile, candidate: CandidateUpdate) -> None:
    """Apply add and remove mutations to important_terms with case-insensitive dedup."""
    existing_keys = {term.strip().casefold() for term in profile.important_terms if term.strip()}

    # Remove terms requested for deletion
    if candidate.proposal.remove:
        remove_keys = {
            (item.get("name") or "").strip().casefold()
            for item in candidate.proposal.remove
            if (item.get("name") or "").strip()
        }
        if remove_keys:
            profile.important_terms = [
                term
                for term in profile.important_terms
                if term.strip().casefold() not in remove_keys
            ]
            # Rebuild existing_keys from updated list
            existing_keys = {
                term.strip().casefold() for term in profile.important_terms if term.strip()
            }

    # Add new terms
    for item in candidate.proposal.items:
        name = (item.get("name") or "").strip()
        if not name:
            continue
        key = name.casefold()
        if key in existing_keys:
            continue
        profile.important_terms.append(name)
        existing_keys.add(key)
    for item in candidate.proposal.add:
        text = str(item).strip()
        if not text:
            continue
        key = text.casefold()
        if key in existing_keys:
            continue
        profile.important_terms.append(text)
        existing_keys.add(key)


def _merge_knowledge(profile: SayaneProfile, candidate: CandidateUpdate) -> None:
    if profile.knowledge is None:
        profile.knowledge = Knowledge(concepts=[])
    for item in candidate.proposal.add:
        if item and item not in profile.knowledge.concepts:
            profile.knowledge.concepts.append(item)


def _merge_values(profile: SayaneProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.values.core:
            profile.values.core.append(item)


def _merge_tone(profile: SayaneProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.voice.tone:
            profile.voice.tone.append(item)


def _merge_roles(profile: SayaneProfile, candidate: CandidateUpdate) -> None:
    for item in candidate.proposal.add:
        if item and item not in profile.identity.roles:
            profile.identity.roles.append(item)


def _merge_policy_list(
    profile: SayaneProfile,
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


def _merge_major_projects(
    profile: SayaneProfile,
    candidate: CandidateUpdate,
) -> None:
    existing_names = {item.name for item in profile.major_projects}
    for item in candidate.proposal.items:
        name = item.get("name", "").strip()
        if not name or name in existing_names:
            continue
        profile.major_projects.append(
            MajorProject(name=name, summary=item.get("summary")),
        )
        existing_names.add(name)


def _merge_communication_mode(
    profile: SayaneProfile,
    candidate: CandidateUpdate,
) -> None:
    mode = profile.communication_mode or CommunicationMode()
    existing_styles = set(mode.collaboration_style)
    for item in candidate.proposal.items:
        path = item.get("path", "").strip()
        value = item.get("value", "").strip()
        if not path or not value:
            continue
        if path == "communication_mode.assistant_name_for_chatgpt":
            mode.assistant_name_for_chatgpt = value
        elif path == "communication_mode.preferred_address":
            mode.preferred_address = value
        elif path == "communication_mode.intimate_address":
            mode.intimate_address = value
        elif path == "communication_mode.collaboration_style":
            if value not in existing_styles:
                mode.collaboration_style.append(value)
                existing_styles.add(value)
    profile.communication_mode = mode
