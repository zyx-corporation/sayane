"""Authorization guards for RDE evaluation and merge decisions."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sayane.core.authorization import (
    FORBIDDEN_ACCOUNTABILITY_PURPOSES,
    AccountabilityDisclosure,
    AccountabilityLog,
    AccountabilityProportionality,
    AccountabilityScope,
    AuthorizationFeatureFlags,
    CumulativeDrift,
    DispositionStatus,
    EvaluatorDescriptor,
    EvaluatorPosition,
    EvaluationSeparation,
    PolicyProvenance,
    UserAuthorizationAudit,
)

if TYPE_CHECKING:
    from sayane.core.candidate import CandidateEvaluation, CandidateUpdate

DEFAULT_GENERATOR_ID = "sayane.capture"
HEURISTIC_EVALUATOR_ID = "sayane.heuristic_rde"
SELF_AGENT_TYPE = "self_agent"

HIGH_REUSE_WEIGHT_THRESHOLD = 0.7


class AuthorizationGuardError(ValueError):
    """Blocked action under authorization layer rules."""


class PopUidLinkageDeferredError(AuthorizationGuardError):
    """PoP-UID must not be linked to authorization/accountability logs yet."""


def default_feature_flags() -> AuthorizationFeatureFlags:
    return AuthorizationFeatureFlags()


def apply_r1_separation_downgrade(
    evaluator: EvaluatorDescriptor,
    separation: EvaluationSeparation,
) -> EvaluatorDescriptor:
    """R1: same generator and evaluator → authority capped at advisory."""
    if separation.generator_id.strip() == separation.evaluator_id.strip():
        position = evaluator.position or EvaluatorPosition()
        if position.authority not in ("advisory",):
            position = position.model_copy(update={"authority": "advisory"})
        evaluator = evaluator.model_copy(update={"position": position})
    return evaluator


def build_heuristic_evaluator(evaluator_id: str = HEURISTIC_EVALUATOR_ID) -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        type=SELF_AGENT_TYPE,
        identity=evaluator_id,
        position=EvaluatorPosition(
            stake="self_interest",
            authority="advisory",
            jurisdiction=["sayane.candidate"],
        ),
        conflict_of_interest="low",
    )


def build_independent_rde_evaluator(model_name: str) -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        type="independent_rde",
        identity=f"llm:{model_name}",
        position=EvaluatorPosition(
            stake="neutral",
            authority="primary",
            jurisdiction=["sayane.candidate"],
        ),
        conflict_of_interest="none",
    )


def build_user_evaluator(actor_id: str = "local_user") -> EvaluatorDescriptor:
    return EvaluatorDescriptor(
        type="user",
        identity=actor_id,
        position=EvaluatorPosition(
            stake="neutral",
            authority="final",
            jurisdiction=["sayane.profile_merge"],
        ),
        conflict_of_interest="none",
    )


def build_separation(
    generator_id: str,
    evaluator_id: str,
) -> EvaluationSeparation:
    gen = generator_id.strip() or DEFAULT_GENERATOR_ID
    ev = evaluator_id.strip() or HEURISTIC_EVALUATOR_ID
    return EvaluationSeparation(
        generator_id=gen,
        evaluator_id=ev,
        is_separated=gen != ev,
    )


def resolve_disposition_status(
    evaluator: EvaluatorDescriptor | None,
    *,
    supplemental_evaluators: list[EvaluatorDescriptor] | None = None,
) -> DispositionStatus:
    """R4/R5: missing position or single self-interested eval stays provisional."""
    if evaluator is None:
        return "provisional"

    all_evaluators = [evaluator, *(supplemental_evaluators or [])]

    if any(ev.position is None for ev in all_evaluators):
        return "provisional"

    confirming = [
        ev
        for ev in all_evaluators
        if ev.position is not None
        and ev.position.authority in ("primary", "final", "veto")
        and ev.position.stake in ("neutral", "third_party_advocate")
        and ev.conflict_of_interest in ("none", "low")
        and ev.type in ("independent_rde", "user", "policy", "council")
    ]
    if confirming:
        return "confirmed"

    if len(all_evaluators) == 1:
        ev = all_evaluators[0]
        pos = ev.position
        if pos is None:
            return "provisional"
        if pos.stake == "self_interest" or ev.conflict_of_interest == "high":
            return "provisional"
        if ev.type == SELF_AGENT_TYPE and pos.authority == "advisory":
            return "provisional"

    return "provisional"


def evaluation_allows_final_action(
    evaluation: CandidateEvaluation | None,
    *,
    supplemental: list[CandidateEvaluation] | None = None,
) -> bool:
    if evaluation is None:
        return False
    if evaluation.disposition_status == "confirmed":
        return True
    extras = supplemental or []
    for extra in extras:
        if extra.disposition_status == "confirmed":
            return True
    primary = evaluation.evaluator
    if primary is None:
        return False
    if primary.position and primary.position.authority in ("primary", "final", "veto"):
        if primary.type in ("user", "policy", "council", "independent_rde"):
            if primary.position.stake in ("neutral", "third_party_advocate"):
                return True
    for extra in extras:
        ev = extra.evaluator
        if ev and ev.position and ev.position.authority in ("primary", "final", "veto"):
            if ev.type in ("user", "policy", "council", "independent_rde"):
                return True
    return False


def user_authorization_status(
    audits: list[UserAuthorizationAudit],
) -> DispositionStatus:
    """R6: high reuse_weight keeps authorization provisional; mirror is not veto."""
    if not audits:
        return "provisional"
    if any(a.reuse_weight >= HIGH_REUSE_WEIGHT_THRESHOLD for a in audits):
        return "provisional"
    if all(a.disposition == "mirror" for a in audits):
        return "provisional"
    return "provisional"


def record_user_authorization_audit(
    *,
    actor_id: str = "local_user",
    reuse_weight: float = 0.0,
    convenience_bias: str = "unknown",
) -> UserAuthorizationAudit:
    bias: str = convenience_bias if convenience_bias in ("none", "low", "high", "unknown") else "unknown"
    status: DispositionStatus = (
        "provisional"
        if reuse_weight >= HIGH_REUSE_WEIGHT_THRESHOLD
        else "provisional"
    )
    return UserAuthorizationAudit(
        convenience_bias=bias,  # type: ignore[arg-type]
        reuse_weight=reuse_weight,
        cumulative_drift=CumulativeDrift(),
        disposition="mirror",
        status=status,
        recorded_at=datetime.now(UTC),
        actor_id=actor_id,
        action="approve_requested",
    )


def mirror_is_not_veto(audit: UserAuthorizationAudit) -> bool:
    return audit.disposition == "mirror"


def validate_accountability_purpose_binding(purposes: list[str]) -> None:
    forbidden = {p.lower() for p in purposes} & FORBIDDEN_ACCOUNTABILITY_PURPOSES
    if forbidden:
        raise AuthorizationGuardError(
            f"Forbidden accountability purpose_binding: {sorted(forbidden)}",
        )


def build_accountability_log(
    *,
    event: str,
    destructive_deviation: bool,
    retention: str = "90d",
    proportionality_note: str = "destructive deviation only",
) -> AccountabilityLog | None:
    """R7: out-of-scope events are not recorded by the institution."""
    scope_in = destructive_deviation
    log = AccountabilityLog(
        scope=AccountabilityScope(
            institutional_interest="destructive_deviation_only",
            in_scope=scope_in,
            delegated_to="human_mediation",
            threshold_note=(
                "Institutional record only for destructive deviation; "
                "non-destructive relations delegated to human mediation."
            ),
        ),
        recorded=scope_in,
        purpose_binding=["accountability"],
        proportionality=AccountabilityProportionality(
            note=proportionality_note,
            retention=retention if scope_in else "",
        ),
        disclosure=AccountabilityDisclosure(procedure_required=True),
        created_at=datetime.now(UTC),
        event=event,
    )
    if not scope_in:
        return None
    validate_accountability_purpose_binding(
        [str(p) for p in log.purpose_binding],
    )
    if not log.proportionality.retention.strip():
        raise AuthorizationGuardError(
            "Accountability log retention must be set when in_scope",
        )
    return log


def assert_external_disclosure_allowed(log: AccountabilityLog) -> None:
    if log.disclosure.procedure_required is False:
        raise AuthorizationGuardError(
            "External disclosure requires procedure_required=true",
        )


def assert_pop_uid_linkage_disabled(
    flags: AuthorizationFeatureFlags | None = None,
    *,
    operation: str = "link",
) -> None:
    """PoP-UID ↔ authorization/accountability join is explicitly deferred."""
    flags = flags or default_feature_flags()
    if flags.pop_uid_linkage_enabled:
        raise PopUidLinkageDeferredError(
            f"PoP-UID linkage is deferred; refused {operation}. "
            "Irreversible tracking infrastructure must not be enabled by default.",
        )


def assert_memory_write_allowed(
    candidate: CandidateUpdate,
    flags: AuthorizationFeatureFlags | None = None,
) -> None:
    """Block profile merge when R1/R4/R5/R6 guards fail."""
    flags = flags or default_feature_flags()
    if not flags.enforce_authorization_guards:
        return

    evaluation = candidate.evaluation
    legacy = evaluation is not None and evaluation.evaluator is None
    if legacy and flags.legacy_approve_compat:
        return

    if evaluation is None:
        raise AuthorizationGuardError(
            "Evaluation required before irreversible profile merge",
        )

    if not evaluation_allows_final_action(evaluation):
        raise AuthorizationGuardError(
            "Evaluation disposition is provisional or advisory-only; "
            "independent, user, policy, or council confirmation required",
        )

    audits = candidate.user_authorization_audits
    if not audits:
        raise AuthorizationGuardError(
            "User authorization audit required (necessary but not sufficient)",
        )

    if not all(mirror_is_not_veto(a) for a in audits):
        raise AuthorizationGuardError("Mirror disposition must not act as veto")

    auth_status = user_authorization_status(audits)
    if auth_status == "provisional" and evaluation.disposition_status != "confirmed":
        if not flags.legacy_approve_compat:
            raise AuthorizationGuardError(
                "User authorization remains provisional (reuse_weight or drift policy)",
            )


def attach_evaluation_authorization(
    evaluation: CandidateEvaluation,
    *,
    generator_id: str,
    evaluator: EvaluatorDescriptor,
    supplemental_evaluators: list[EvaluatorDescriptor] | None = None,
) -> CandidateEvaluation:
    separation = build_separation(generator_id, evaluator.identity)
    evaluator = apply_r1_separation_downgrade(evaluator, separation)
    disposition = resolve_disposition_status(
        evaluator,
        supplemental_evaluators=supplemental_evaluators,
    )
    return evaluation.model_copy(
        update={
            "evaluator": evaluator,
            "separation": separation,
            "policy_provenance": PolicyProvenance(),
            "disposition_status": disposition,
        },
    )
