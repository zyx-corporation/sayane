"""Merge heuristic and LLM RDE classifications conservatively."""

from omomuki.core.candidate import LLMReview, RDEClass

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
) -> tuple[RDEClass, list[str]]:
    """Pick the more conservative (higher severity) classification."""
    if llm is None or llm.rde_class is None:
        return heuristic, []

    llm_class = llm.rde_class
    if _SEVERITY[llm_class] >= _SEVERITY[heuristic]:
        notes = [f"LLM judge ({llm.model}): {llm_class}"]
        notes.extend(llm.notes)
        if llm_class != heuristic:
            notes.insert(0, f"Heuristic was {heuristic}; merged to {llm_class}.")
        return llm_class, notes

    return heuristic, [
        f"LLM judge suggested {llm_class}; kept heuristic {heuristic}.",
        *llm.notes,
    ]
