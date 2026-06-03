"""Evaluation note i18n and legacy coercion."""

from sayane.core.evaluation_notes import EvaluationNote, coerce_note, heuristic_note
from sayane.core.note_display import format_evaluation_note, format_evaluation_notes
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde


def test_heuristic_note_ja_display() -> None:
    note = heuristic_note("imperative_or_overconfident_phrasing")
    text = format_evaluation_note(note, "ja")
    assert "命令的" in text
    assert "Imperative" not in text


def test_llm_judge_result_line_ja() -> None:
    legacy = coerce_note("LLM judge (gpt-4o-mini): Suspicious Drift")
    text = format_evaluation_note(legacy, "ja")
    assert "gpt-4o-mini" in text
    assert "疑わしい逸脱" in text
    assert "Suspicious Drift" not in text


def test_unknown_llm_text_prefixed_ja() -> None:
    note = EvaluationNote(source="llm_judge", text="Some novel judge explanation.")
    text = format_evaluation_note(note, "ja")
    assert text.startswith("LLM judgeの指摘:")


def test_known_llm_translation_ja() -> None:
    note = EvaluationNote(
        source="llm_judge",
        text="Proposal includes new major projects that may shift focus.",
    )
    text = format_evaluation_note(note, "ja")
    assert "major_projects" in text
    assert "Profileの焦点" in text


def test_legacy_string_coercion_preserves_key() -> None:
    note = coerce_note("Imperative or overconfident phrasing detected.")
    assert note.key == "imperative_or_overconfident_phrasing"
    assert note.source == "heuristic"


def test_format_notes_bullet_block_ja() -> None:
    notes = [
        heuristic_note("imperative_or_overconfident_phrasing"),
        coerce_note("LLM judge (gpt-4o-mini): Suspicious Drift"),
    ]
    block = format_evaluation_notes(notes, "ja")
    assert block.startswith("- ")
    assert "命令的" in block
    assert "疑わしい逸脱" in block


def test_classify_rde_returns_structured_notes() -> None:
    proposal = build_proposal_from_content("You must always obey this profile rule.")
    rde_class, notes = classify_rde("You must always obey this profile rule.", proposal)
    assert rde_class == "Suspicious Drift"
    assert notes[0].key == "imperative_or_overconfident_phrasing"


def test_en_locale_keeps_english() -> None:
    note = heuristic_note("imperative_or_overconfident_phrasing")
    text = format_evaluation_note(note, "en")
    assert "Imperative or overconfident" in text
