"""Merge heuristic and LLM RDE classifications conservatively."""

from sayane.core.candidate import CandidateProposal, LLMReview, RDEClass
from sayane.core.evaluation_notes import EvaluationNote, heuristic_note
from sayane.evaluators.list_diff import list_diff_for_important_terms, list_diff_operation

_SEVERITY: dict[RDEClass, int] = {
    "Preserved": 0,
    "Authorized Transformation": 1,
    "Inferred Extension": 2,
    "Unresolved Gap": 3,
    "Suspicious Drift": 4,
    "Critical Distortion": 5,
}

_IMPORTANT_TERMS_LIST_ADD_HEURISTICS: frozenset[RDEClass] = frozenset(
    {
        "Preserved",
        "Authorized Transformation",
        "Inferred Extension",
    }
)


def _is_important_terms_list_add_only(proposal: CandidateProposal | None) -> bool:
    if proposal is None or proposal.section != "important_terms":
        return False
    diff = list_diff_for_important_terms(proposal)
    return list_diff_operation(diff) == "list_add" and not diff.removed


def _cap_llm_class_for_important_terms_list_add(
    heuristic: RDEClass,
    llm_class: RDEClass,
    proposal: CandidateProposal | None,
) -> RDEClass:
    """Append-only important_terms merges are not escalated to Suspicious Drift by LLM alone."""
    if not _is_important_terms_list_add_only(proposal):
        return llm_class
    if llm_class == "Critical Distortion":
        return llm_class
    if heuristic not in _IMPORTANT_TERMS_LIST_ADD_HEURISTICS:
        return llm_class
    if _SEVERITY[llm_class] > _SEVERITY[heuristic]:
        return heuristic
    return llm_class


def merge_rde_class(
    heuristic: RDEClass,
    llm: LLMReview | None,
    *,
    proposal: CandidateProposal | None = None,
) -> tuple[RDEClass, list[EvaluationNote]]:
    """Pick the more conservative (higher severity) classification."""
    if llm is None or llm.rde_class is None:
        return heuristic, []

    llm_class = llm.rde_class
    effective_llm = _cap_llm_class_for_important_terms_list_add(
        heuristic,
        llm_class,
        proposal,
    )
    capped = effective_llm != llm_class

    if capped:
        notes: list[EvaluationNote] = [
            heuristic_note(
                "llm_judge_capped_important_terms_list_add",
                llm_rde_class=llm_class,
                rde_class=effective_llm,
            ),
            heuristic_note(
                "llm_judge_result",
                model=llm.model,
                rde_class=llm_class,
            ),
        ]
        notes.extend(llm.notes)
        return effective_llm, notes

    if _SEVERITY[effective_llm] >= _SEVERITY[heuristic]:
        notes: list[EvaluationNote] = [
            heuristic_note(
                "llm_judge_result",
                model=llm.model,
                rde_class=effective_llm,
            ),
        ]
        notes.extend(llm.notes)
        if effective_llm != heuristic:
            notes.insert(
                0,
                heuristic_note(
                    "heuristic_merged_to_llm",
                    heuristic=heuristic,
                    rde_class=effective_llm,
                ),
            )
        return effective_llm, notes

    return heuristic, [
        heuristic_note(
            "llm_judge_suggested_kept_heuristic",
            rde_class=effective_llm,
            heuristic=heuristic,
        ),
        *llm.notes,
    ]
