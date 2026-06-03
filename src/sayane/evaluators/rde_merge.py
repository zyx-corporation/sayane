"""Merge heuristic and LLM RDE classifications conservatively."""

from sayane.core.candidate import LLMReview, RDEClass
from sayane.core.evaluation_notes import EvaluationNote, heuristic_note

_SEVERITY: dict[RDEClass, int] = {
    "Preserved": 0,
    "Authorized Transformation": 1,
    "Inferred Extension": 2,
    "Unresolved Gap": 3,
    "Suspicious Drift": 4,
    "Critical Distortion": 5,
}


def merge_rde_class(
    heuristic: RDEClass,
    llm: LLMReview | None,
) -> tuple[RDEClass, list[EvaluationNote]]:
    """Pick the more conservative (higher severity) classification."""
    if llm is None or llm.rde_class is None:
        return heuristic, []

    llm_class = llm.rde_class
    if _SEVERITY[llm_class] >= _SEVERITY[heuristic]:
        notes: list[EvaluationNote] = [
            heuristic_note(
                "llm_judge_result",
                model=llm.model,
                rde_class=llm_class,
            ),
        ]
        notes.extend(llm.notes)
        if llm_class != heuristic:
            notes.insert(
                0,
                heuristic_note(
                    "heuristic_merged_to_llm",
                    heuristic=heuristic,
                    rde_class=llm_class,
                ),
            )
        return llm_class, notes

    return heuristic, [
        heuristic_note(
            "llm_judge_suggested_kept_heuristic",
            rde_class=llm_class,
            heuristic=heuristic,
        ),
        *llm.notes,
    ]
