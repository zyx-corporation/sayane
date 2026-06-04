"""Candidate evaluation, approve, and reject orchestration."""

from datetime import UTC, datetime

from sayane.bridge.config import BridgeConfig
from sayane.bridge.service import resolve_profile_path
from sayane.core.candidate import (
    CandidateEvaluation,
    CandidateEvaluationError,
    CandidateUpdate,
)
from sayane.core.authorization import EvaluatorDescriptor
from sayane.core.evaluation_notes import heuristic_note
from sayane.core.loader import load_profile
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.judge_config import load_judge_config
from sayane.evaluators.llm_judge import (
    LLMJudgeRequestError,
    review_with_llm,
)
from sayane.evaluators.merge import merge_candidate_into_profile
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.evaluators.rde_merge import merge_rde_class
from sayane.evaluators.sections import can_merge_section
from sayane.evaluators.uib import score_uib
from sayane.evaluators.authorization_guards import (
    DEFAULT_GENERATOR_ID,
    attach_evaluation_authorization,
    build_accountability_log,
    build_heuristic_evaluator,
    build_independent_rde_evaluator,
    build_user_evaluator,
    default_feature_flags,
    assert_memory_write_allowed,
    record_user_authorization_audit,
)
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
    if not candidate.proposal.add and not candidate.proposal.items:
        profile_path = resolve_profile_path(config, candidate.target_profile_id)
        profile = load_profile(profile_path)
        candidate.proposal = build_proposal_from_content(
            candidate.content,
            profile=profile,
        )

    heuristic_class, heuristic_notes = classify_rde(
        candidate.content,
        candidate.proposal,
    )
    uib = score_uib(candidate.content, candidate.proposal)
    notes = list(heuristic_notes)
    llm_review = None
    candidate.evaluation_error = None

    if level >= 2:
        judge_cfg = load_judge_config(level)
        if judge_cfg is None:
            notes.append(
                heuristic_note(
                    "llm_judge_skipped",
                    detail=(
                        f"Level {level} LLM judge skipped: configure ~/.sayane/judge.yaml "
                        "or SAYANE_JUDGE_* environment variables."
                    ),
                ),
            )
        else:
            profile_path = resolve_profile_path(
                config,
                candidate.target_profile_id,
            )
            profile = load_profile(profile_path)
            try:
                llm_review = review_with_llm(
                    judge_cfg,
                    level,
                    profile,
                    candidate.content,
                    candidate.proposal,
                    locale=candidate.locale,
                )
                if llm_review.uib is not None:
                    uib = llm_review.uib
            except LLMJudgeRequestError as exc:
                candidate.status = "pending"
                candidate.evaluation_status = "judge_failed"
                candidate.evaluation = None
                candidate.evaluation_error = _judge_error_payload(exc)
                save_candidate(config, candidate)
                return candidate
            except (RuntimeError, ValueError, KeyError) as exc:
                notes.append(heuristic_note("llm_judge_failed", detail=str(exc)))

    final_class, merge_notes = merge_rde_class(
        heuristic_class,
        llm_review,
        proposal=candidate.proposal,
    )
    notes.extend(merge_notes)

    candidate.evaluation = CandidateEvaluation(
        level=level,
        rde_class=final_class,
        notes=notes,
        uib=uib,
        evaluated_at=datetime.now(UTC),
        llm_review=llm_review,
    )
    generator_id = candidate.generator_id or DEFAULT_GENERATOR_ID
    heuristic_ev = build_heuristic_evaluator()
    supplemental: list[EvaluatorDescriptor] = []
    if llm_review is not None:
        supplemental.append(build_independent_rde_evaluator(llm_review.model))

    candidate.evaluation = attach_evaluation_authorization(
        candidate.evaluation,
        generator_id=generator_id,
        evaluator=heuristic_ev,
        supplemental_evaluators=supplemental,
    )
    if llm_review is not None:
        llm_eval = attach_evaluation_authorization(
            CandidateEvaluation(
                level=llm_review.level,
                rde_class=llm_review.rde_class or final_class,
                notes=llm_review.notes,
                uib=llm_review.uib or uib,
                evaluated_at=datetime.now(UTC),
            ),
            generator_id=generator_id,
            evaluator=build_independent_rde_evaluator(llm_review.model),
        )
        candidate.supplemental_evaluations = [llm_eval]
        if llm_eval.disposition_status == "confirmed":
            candidate.evaluation = candidate.evaluation.model_copy(
                update={"disposition_status": "confirmed"},
            )

    if final_class == "Critical Distortion":
        log = build_accountability_log(
            event="critical_distortion_detected",
            destructive_deviation=True,
        )
        if log is not None:
            candidate.accountability_logs.append(log)

    candidate.status = "evaluated"
    candidate.evaluation_status = "completed"
    save_candidate(config, candidate)
    return candidate


def approve_candidate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
    override_reason: str | None = None,
) -> CandidateUpdate:
    candidate = load_candidate(config, candidate_id)
    if candidate.status == "approved":
        return candidate
    if candidate.evaluation is None:
        candidate = evaluate_candidate(config, candidate_id)

    if (
        candidate.evaluation
        and candidate.evaluation.rde_class == "Critical Distortion"
    ):
        if not force_critical:
            raise ValueError(
                "Cannot approve Critical Distortion without --force-critical. "
                "Reject or edit profile manually.",
            )

    from sayane.plugins.hooks import run_before_candidate_approve

    run_before_candidate_approve(config, candidate)

    flags = default_feature_flags()
    reuse_weight = _estimate_reuse_weight(candidate)
    candidate.user_authorization_audits.append(
        record_user_authorization_audit(reuse_weight=reuse_weight),
    )
    user_eval = build_user_evaluator()
    candidate.supplemental_evaluations.append(
        attach_evaluation_authorization(
            CandidateEvaluation(
                level=0,
                rde_class=candidate.evaluation.rde_class if candidate.evaluation else "Preserved",
                notes=[],
                uib=candidate.evaluation.uib if candidate.evaluation else score_uib("", candidate.proposal),
                evaluated_at=datetime.now(UTC),
            ),
            generator_id=candidate.generator_id or DEFAULT_GENERATOR_ID,
            evaluator=user_eval,
        ),
    )
    if candidate.evaluation and candidate.supplemental_evaluations:
        last = candidate.supplemental_evaluations[-1]
        if last.disposition_status == "confirmed":
            candidate.evaluation = candidate.evaluation.model_copy(
                update={"disposition_status": "confirmed"},
            )

    assert_memory_write_allowed(candidate, flags)

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
            "rde_class": (
                candidate.evaluation.rde_class if candidate.evaluation else None
            ),
            "evaluation_level": (
                candidate.evaluation.level if candidate.evaluation else None
            ),
            "section": candidate.proposal.section,
            "added": candidate.proposal.add,
            "force_critical": force_critical,
            **(
                {"override_reason": override_reason}
                if override_reason
                else {}
            ),
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


def _judge_error_payload(
    exc: LLMJudgeRequestError,
) -> CandidateEvaluationError:
    status_code = exc.status_code
    if status_code == 401:
        err_type = "llm_judge_auth_error"
    elif status_code == 403:
        err_type = "llm_judge_permission_error"
    elif status_code == 429:
        err_type = "llm_judge_rate_limit"
    elif status_code in {500, 502, 503}:
        err_type = "llm_judge_provider_unavailable"
    else:
        err_type = "llm_judge_request_error"

    return CandidateEvaluationError(
        type=err_type,
        message=str(exc),
        provider=exc.provider,
        status_code=status_code,
    )


def _estimate_reuse_weight(candidate: CandidateUpdate) -> float:
    """Heuristic reuse signal for R6 (feature-flaggable / immature logic)."""
    if candidate.capture_meta and candidate.capture_meta.capture_source == "page":
        return 0.75
    if candidate.capture_meta and candidate.capture_meta.capture_confidence == "low":
        return 0.6
    return 0.2
