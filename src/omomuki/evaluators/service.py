"""Candidate evaluation, approve, and reject orchestration."""

from datetime import UTC, datetime

import yaml

from omomuki.bridge.config import BridgeConfig
from omomuki.bridge.service import resolve_profile_path
from omomuki.core.candidate import CandidateEvaluation, CandidateUpdate
from omomuki.core.loader import load_profile
from omomuki.evaluators.diff import profile_diff_for_candidate
from omomuki.evaluators.merge import merge_candidate_into_profile
from omomuki.evaluators.proposal import build_proposal_from_content
from omomuki.evaluators.rde import classify_rde
from omomuki.evaluators.uib import score_uib
from omomuki.storage.candidates import load_candidate, save_candidate
from omomuki.storage.lineage_store import append_record


def evaluate_candidate(config: BridgeConfig, candidate_id: str) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    if not candidate.proposal.add:
        candidate.proposal = build_proposal_from_content(candidate.content)

    rde_class, notes = classify_rde(candidate.content, candidate.proposal)
    uib = score_uib(candidate.content, candidate.proposal)
    candidate.evaluation = CandidateEvaluation(
        rde_class=rde_class,
        notes=notes,
        uib=uib,
        evaluated_at=datetime.now(UTC),
    )
    candidate.status = "evaluated"
    save_candidate(config, candidate)
    return candidate


def approve_candidate(config: BridgeConfig, candidate_id: str) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    if candidate.status == "approved":
        return candidate
    if candidate.evaluation is None:
        candidate = evaluate_candidate(config, candidate_id)

    if candidate.evaluation and candidate.evaluation.rde_class == "Critical Distortion":
        raise ValueError(
            "Cannot auto-approve Critical Distortion. Reject or edit profile manually.",
        )

    profile_path = resolve_profile_path(config, candidate.target_profile_id)
    profile = load_profile(profile_path)
    updated = merge_candidate_into_profile(profile, candidate)
    profile_path.write_text(
        yaml.safe_dump(
            updated.model_dump(mode="json"),
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    candidate.status = "approved"
    save_candidate(config, candidate)

    append_record(
        config,
        candidate.target_profile_id,
        "candidate_approved",
        {
            "candidate_id": candidate.id,
            "rde_class": candidate.evaluation.rde_class if candidate.evaluation else None,
            "section": candidate.proposal.section,
            "added": candidate.proposal.add,
        },
    )
    return candidate


def reject_candidate(
    config: BridgeConfig,
    candidate_id: str,
    reason: str | None = None,
) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    candidate.status = "rejected"
    save_candidate(config, candidate)
    append_record(
        config,
        candidate.target_profile_id,
        "candidate_rejected",
        {"candidate_id": candidate.id, "reason": reason},
    )
    return candidate


def diff_candidate(config: BridgeConfig, candidate_id: str) -> dict:
    candidate = load_candidate(config, candidate_id)
    profile_path = resolve_profile_path(config, candidate.target_profile_id)
    profile = load_profile(profile_path)
    return profile_diff_for_candidate(profile, candidate)
