"""Structured RDE evaluation notes (heuristic keys + LLM free text)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

NoteSource = Literal["heuristic", "llm_judge"]


class EvaluationNote(BaseModel):
    """Stored evaluation note; display text is resolved at read time by locale."""

    model_config = ConfigDict(extra="forbid")

    source: NoteSource
    key: str | None = None
    params: dict[str, Any] = Field(default_factory=dict)
    text: str | None = None


_LEGACY_NOTE_KEYS: dict[str, str] = {
    "Content references critical profile fields or secrets.": (
        "content_references_critical_profile_fields"
    ),
    "Identity-related change detected.": "identity_related_change_detected",
    "Capture too short for reliable merge judgment.": "capture_too_short",
    "Multiple profile sections mixed in one capture.": "multiple_profile_sections_mixed",
    "Proposal overlaps existing profile entries across sections.": (
        "proposal_overlaps_existing_across_sections"
    ),
    "Imperative or overconfident phrasing detected.": (
        "imperative_or_overconfident_phrasing"
    ),
    "Proposal contains project-style items in knowledge.concepts.": (
        "project_items_in_concepts"
    ),
    "Potential redundancy with existing major_projects context.": (
        "potential_redundancy_with_major_projects"
    ),
    "No effective profile update: duplicate major_projects items.": (
        "no_effective_profile_update_major_projects"
    ),
    "Project updates inferred from capture structure.": "project_updates_inferred",
    "No effective profile update: duplicate communication_mode values.": (
        "no_effective_profile_update_communication_mode"
    ),
    "communication_mode updates require manual review.": (
        "communication_mode_requires_manual_review"
    ),
    "communication_mode-derived values should not be added to knowledge.concepts.": (
        "communication_mode_values_in_concepts"
    ),
    "No concrete proposal items extracted.": "no_concrete_proposal_items",
    "Non-critical knowledge extension from capture.": (
        "non_critical_knowledge_extension"
    ),
    "Section change requires manual review.": "section_change_requires_manual_review",
    "Proposal adds existing projects without clear justification.": (
        "proposal_adds_existing_projects"
    ),
    "Potential for redundancy in knowledge.concepts.": (
        "potential_redundancy_in_concepts"
    ),
}


def heuristic_note(key: str, **params: Any) -> EvaluationNote:
    return EvaluationNote(source="heuristic", key=key, params=params)


def llm_text_note(text: str) -> EvaluationNote:
    return EvaluationNote(source="llm_judge", text=text.strip())


def llm_key_note(key: str, **params: Any) -> EvaluationNote:
    return EvaluationNote(source="llm_judge", key=key, params=params)


def coerce_note(item: Any) -> EvaluationNote:
    if isinstance(item, EvaluationNote):
        return item
    if isinstance(item, dict):
        return EvaluationNote.model_validate(item)
    if isinstance(item, str):
        stripped = item.strip()
        legacy_key = _LEGACY_NOTE_KEYS.get(stripped)
        if legacy_key:
            return heuristic_note(legacy_key)
        merged = _parse_merge_line(stripped)
        if merged:
            return merged
        judge = _parse_llm_judge_line(stripped)
        if judge:
            return judge
        if stripped.startswith("Level ") and "LLM judge skipped" in stripped:
            return heuristic_note("llm_judge_skipped", detail=stripped)
        if stripped.startswith("LLM judge failed:"):
            return heuristic_note("llm_judge_failed", detail=stripped)
        return llm_text_note(stripped)
    raise TypeError(f"Unsupported note type: {type(item)!r}")


def coerce_notes(items: list[Any]) -> list[EvaluationNote]:
    return [coerce_note(item) for item in items]


def _parse_merge_line(line: str) -> EvaluationNote | None:
    prefix = "Heuristic was "
    mid = "; merged to "
    if line.startswith(prefix) and mid in line:
        rest = line[len(prefix) :]
        heuristic, llm_class = rest.split(mid, 1)
        return heuristic_note(
            "heuristic_merged_to_llm",
            heuristic=heuristic.strip(),
            rde_class=llm_class.strip().rstrip("."),
        )
    prefix2 = "LLM judge suggested "
    mid2 = "; kept heuristic "
    if line.startswith(prefix2) and mid2 in line:
        rest = line[len(prefix2) :]
        llm_class, heuristic = rest.split(mid2, 1)
        return heuristic_note(
            "llm_judge_suggested_kept_heuristic",
            rde_class=llm_class.strip(),
            heuristic=heuristic.strip().rstrip("."),
        )
    return None


def _parse_llm_judge_line(line: str) -> EvaluationNote | None:
    if not line.startswith("LLM judge (") or ": " not in line:
        return None
    try:
        paren_end = line.index(")")
        model = line[len("LLM judge (") : paren_end]
        rde_class = line.split(": ", 1)[1].strip()
        return llm_key_note("llm_judge_result", model=model, rde_class=rde_class)
    except ValueError:
        return None
