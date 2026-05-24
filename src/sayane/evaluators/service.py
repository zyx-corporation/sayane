"""Candidate evaluation, approve, and reject orchestration."""

from datetime import UTC, datetime

from sayane.bridge.config import BridgeConfig
from sayane.bridge.service import resolve_profile_path
from sayane.core.candidate import CandidateEvaluation, CandidateUpdate
from sayane.core.loader import load_profile
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.judge_config import load_judge_config
from sayane.evaluators.llm_judge import review_with_llm
from sayane.evaluators.merge import merge_candidate_into_profile
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.evaluators.rde_merge import merge_rde_class
from sayane.evaluators.sections import can_merge_section
from sayane.evaluators.uib import score_uib
from sayane.storage.candidates import load_candidate, save_candidate
from sayane.storage.git_integration import auto_commit_profile_store
from sayane.storage.lineage_store import append_record


def evaluate_candidate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    level: int = 1,
) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    if not candidate.proposal.add:
        candidate.proposal = build_proposal_from_content(candidate.content)

    heuristic_class, heuristic_notes = classify_rde(candidate.content, candidate.proposal)
    uib = score_uib(candidate.content, candidate.proposal)
    notes = list(heuristic_notes)
    llm_review = None

    if level >= 2:
        judge_cfg = load_judge_config(level)
        if judge_cfg is None:
            notes.append(
                f"Level {level} LLM judge skipped: configure ~/.sayane/judge.yaml "
                "or SAYANE_JUDGE_* environment variables.",
            )
        else:
            profile_path = resolve_profile_path(config, candidate.target_profile_id)
            profile = load_profile(profile_path)
            try:
                llm_review = review_with_llm(
                    judge_cfg,
                    level,
                    profile,
                    candidate.content,
                    candidate.proposal,
                )
                if llm_review.uib is not None:
                    uib = llm_review.uib
            except (RuntimeError, ValueError, KeyError) as exc:
                notes.append(f"LLM judge failed: {exc}")

    final_class, merge_notes = merge_rde_class(heuristic_class, llm_review)
    notes.extend(merge_notes)

    candidate.evaluation = CandidateEvaluation(
        level=level,
        rde_class=final_class,
        notes=notes,
        uib=uib,
        evaluated_at=datetime.now(UTC),
        llm_review=llm_review,
    )
    candidate.status = "evaluated"
    save_candidate(config, candidate)
    return candidate


def approve_candidate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    if candidate.status == "approved":
        return candidate
    if candidate.evaluation is None:
        candidate = evaluate_candidate(config, candidate_id)

    if candidate.evaluation and candidate.evaluation.rde_class == "Critical Distortion":
        if not force_critical:
            raise ValueError(
                "Cannot approve Critical Distortion without --force-critical. "
                "Reject or edit profile manually.",
            )

    from sayane.plugins.hooks import run_before_candidate_approve

    run_before_candidate_approve(config, candidate)

    section = candidate.proposal.section
    if not can_merge_section(section, force_critical=force_critical):
        raise ValueError(
            f"Cannot merge section '{section}' without --force-critical. "
            "Edit profile manually after review.",
        )

    profile_path = resolve_profile_path(config, candidate.target_profile_id)
    from sayane.storage.factory import open_storage

    bundle = open_storage(profile=profile_path, home=config.home)
    profile = bundle.profile.load()
    updated = merge_candidate_into_profile(
        profile,
        candidate,
        force_critical=force_critical,
    )
    bundle.profile.save(updated)
    if bundle.uses_git_auto_commit:
        auto_commit_profile_store(
            bundle.profile.profile_dir,
            f"sayane: approve candidate {candidate.id}",
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
            "evaluation_level": candidate.evaluation.level if candidate.evaluation else None,
            "section": candidate.proposal.section,
            "added": candidate.proposal.add,
            "force_critical": force_critical,
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
