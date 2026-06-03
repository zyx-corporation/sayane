"""Authorization layer guards (R1, R4/R5, R6, R7, PoP-UID deferral)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.core.authorization import (
    AccountabilityLog,
    AuthorizationFeatureFlags,
    EvaluatorDescriptor,
    EvaluatorPosition,
    EvaluationSeparation,
    UserAuthorizationAudit,
)
from sayane.core.candidate import (
    CandidateEvaluation,
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
    UIBScores,
)
from sayane.core.pop_uid import refuse_identity_authorization_join
from sayane.evaluators.authorization_guards import (
    apply_r1_separation_downgrade,
    assert_external_disclosure_allowed,
    assert_memory_write_allowed,
    assert_pop_uid_linkage_disabled,
    attach_evaluation_authorization,
    build_accountability_log,
    build_heuristic_evaluator,
    build_independent_rde_evaluator,
    build_separation,
    build_user_evaluator,
    default_feature_flags,
    evaluation_allows_final_action,
    mirror_is_not_veto,
    record_user_authorization_audit,
    resolve_disposition_status,
    user_authorization_status,
    validate_accountability_purpose_binding,
)
from sayane.evaluators.uib import score_uib


def _uib() -> UIBScores:
    return UIBScores(UD=0.5, MI=0.5, CH=0.5, DT=0.5, VP=0.5, FG=0.5)


def _minimal_candidate(evaluation: CandidateEvaluation | None = None) -> CandidateUpdate:
    return CandidateUpdate(
        id="c-auth",
        status="evaluated",
        target_profile_id="default",
        content="test",
        generator_id="sayane.capture",
        source=CandidateSource(type="test", captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=["x"]),
        evaluation=evaluation,
    )


# --- R1 ---


def test_r1_same_generator_evaluator_downgrades_to_advisory() -> None:
    ev = EvaluatorDescriptor(
        type="self_agent",
        identity="sayane.capture",
        position=EvaluatorPosition(stake="self_interest", authority="final"),
    )
    sep = build_separation("sayane.capture", "sayane.capture")
    downgraded = apply_r1_separation_downgrade(ev, sep)
    assert downgraded.position is not None
    assert downgraded.position.authority == "advisory"


def test_self_agent_eval_alone_stays_provisional() -> None:
    ev = build_heuristic_evaluator()
    sep = build_separation("sayane.capture", ev.identity)
    ev = apply_r1_separation_downgrade(ev, sep)
    assert resolve_disposition_status(ev) == "provisional"


def test_self_agent_only_cannot_allow_final_action() -> None:
    ev = build_heuristic_evaluator()
    sep = build_separation("sayane.capture", ev.identity)
    ev = apply_r1_separation_downgrade(ev, sep)
    evaluation = attach_evaluation_authorization(
        CandidateEvaluation(
            level=1,
            rde_class="Inferred Extension",
            notes=[],
            uib=_uib(),
            evaluated_at=datetime.now(UTC),
        ),
        generator_id="sayane.capture",
        evaluator=ev,
    )
    assert evaluation.disposition_status == "provisional"
    assert not evaluation_allows_final_action(evaluation)


def test_independent_rde_can_confirm_when_separated() -> None:
    indep = build_independent_rde_evaluator("test-model")
    evaluation = attach_evaluation_authorization(
        CandidateEvaluation(
            level=2,
            rde_class="Inferred Extension",
            notes=[],
            uib=_uib(),
            evaluated_at=datetime.now(UTC),
        ),
        generator_id="sayane.capture",
        evaluator=indep,
    )
    assert evaluation.disposition_status == "confirmed"
    assert evaluation_allows_final_action(evaluation)


# --- R4/R5 ---


def test_missing_position_stays_provisional() -> None:
    ev = EvaluatorDescriptor(
        type="independent_rde",
        identity="rde.external",
        position=None,
        conflict_of_interest="none",
    )
    assert resolve_disposition_status(ev) == "provisional"


def test_single_self_interest_stays_provisional() -> None:
    ev = EvaluatorDescriptor(
        type="self_agent",
        identity="agent",
        position=EvaluatorPosition(stake="self_interest", authority="advisory"),
        conflict_of_interest="low",
    )
    assert resolve_disposition_status(ev) == "provisional"


def test_neutral_independent_rde_confirms() -> None:
    ev = build_independent_rde_evaluator("judge")
    assert resolve_disposition_status(ev) == "confirmed"


def test_council_policy_can_confirm() -> None:
    ev = EvaluatorDescriptor(
        type="council",
        identity="council.local",
        position=EvaluatorPosition(stake="neutral", authority="final", jurisdiction=["local"]),
        conflict_of_interest="none",
    )
    assert resolve_disposition_status(ev) == "confirmed"


# --- R6 ---


def test_user_authorization_audit_recorded() -> None:
    audit = record_user_authorization_audit(reuse_weight=0.1)
    assert audit.disposition == "mirror"
    assert audit.recorded_at is not None


def test_high_reuse_weight_keeps_authorization_provisional() -> None:
    audit = record_user_authorization_audit(reuse_weight=0.9)
    assert user_authorization_status([audit]) == "provisional"


def test_mirror_is_not_veto() -> None:
    audit = record_user_authorization_audit()
    assert mirror_is_not_veto(audit)


def test_mirror_does_not_block_when_user_confirms_evaluation() -> None:
    indep = build_independent_rde_evaluator("judge")
    evaluation = attach_evaluation_authorization(
        CandidateEvaluation(
            level=2,
            rde_class="Authorized Transformation",
            notes=[],
            uib=_uib(),
            evaluated_at=datetime.now(UTC),
        ),
        generator_id="sayane.capture",
        evaluator=indep,
    )
    candidate = _minimal_candidate(evaluation)
    candidate.user_authorization_audits.append(record_user_authorization_audit(reuse_weight=0.1))
    flags = AuthorizationFeatureFlags(legacy_approve_compat=False)
    assert_memory_write_allowed(candidate, flags)


# --- R7 ---


def test_out_of_scope_accountability_log_not_recorded() -> None:
    log = build_accountability_log(event="minor_drift", destructive_deviation=False)
    assert log is None


def test_in_scope_accountability_log_recorded() -> None:
    log = build_accountability_log(
        event="critical_distortion",
        destructive_deviation=True,
        retention="1y",
    )
    assert log is not None
    assert log.recorded is True
    assert log.scope.in_scope is True


def test_forbidden_purpose_binding_rejected() -> None:
    with pytest.raises(Exception, match="Forbidden"):
        validate_accountability_purpose_binding(["accountability", "profiling"])


def test_external_disclosure_requires_procedure() -> None:
    log = build_accountability_log(
        event="critical_distortion",
        destructive_deviation=True,
        retention="90d",
    )
    assert log is not None
    log = log.model_copy(
        update={"disclosure": log.disclosure.model_copy(update={"procedure_required": False})},
    )
    with pytest.raises(Exception, match="procedure_required"):
        assert_external_disclosure_allowed(log)


def test_empty_retention_blocks_in_scope_log() -> None:
    with pytest.raises(Exception, match="retention"):
        build_accountability_log(
            event="critical_distortion",
            destructive_deviation=True,
            retention="",
        )


# --- PoP-UID ---


def test_pop_uid_linkage_disabled_by_default() -> None:
    flags = default_feature_flags()
    assert flags.pop_uid_linkage_enabled is False
    assert_pop_uid_linkage_disabled(flags, operation="join")


def test_pop_uid_join_allowed_when_disabled() -> None:
    refuse_identity_authorization_join(operation="export")


def test_pop_uid_enabled_raises_on_link() -> None:
    flags = AuthorizationFeatureFlags(pop_uid_linkage_enabled=True)
    with pytest.raises(Exception, match="deferred"):
        assert_pop_uid_linkage_disabled(flags, operation="linkage")


# --- integration guard ---


def test_approve_blocked_without_user_audit_when_strict() -> None:
    indep = build_independent_rde_evaluator("judge")
    evaluation = attach_evaluation_authorization(
        CandidateEvaluation(
            level=2,
            rde_class="Inferred Extension",
            notes=[],
            uib=_uib(),
            evaluated_at=datetime.now(UTC),
        ),
        generator_id="sayane.capture",
        evaluator=indep,
    )
    candidate = _minimal_candidate(evaluation)
    flags = AuthorizationFeatureFlags(
        enforce_authorization_guards=True,
        legacy_approve_compat=False,
    )
    with pytest.raises(Exception, match="User authorization"):
        assert_memory_write_allowed(candidate, flags)


def test_legacy_evaluation_compat_allows_approve_path() -> None:
    evaluation = CandidateEvaluation(
        level=1,
        rde_class="Inferred Extension",
        notes=[],
        uib=_uib(),
        evaluated_at=datetime.now(UTC),
    )
    candidate = _minimal_candidate(evaluation)
    candidate.user_authorization_audits.append(record_user_authorization_audit())
    flags = default_feature_flags()
    assert_memory_write_allowed(candidate, flags)
