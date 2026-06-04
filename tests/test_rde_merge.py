from sayane.core.candidate import CandidateProposal, LLMReview
from sayane.core.evaluation_notes import llm_text_note
from sayane.evaluators.capture_parse import classify_important_terms_yaml, try_parse_yaml
from sayane.evaluators.rde_merge import merge_rde_class


def _important_terms_proposal() -> CandidateProposal:
    parsed, _ = try_parse_yaml(
        "important_terms:\n"
        '  - "Kotone"\n'
        '  - "RDE"\n'
        '  - "制度的シコファンシー"\n',
    )
    assert isinstance(parsed, dict)
    return classify_important_terms_yaml(parsed, None)


def test_merge_caps_suspicious_drift_for_important_terms_list_add() -> None:
    proposal = _important_terms_proposal()
    llm = LLMReview(
        model="gpt-4o-mini",
        level=2,
        rde_class="Suspicious Drift",
        notes=[llm_text_note("Terms seem unrelated.")],
    )
    final, notes = merge_rde_class(
        "Authorized Transformation",
        llm,
        proposal=proposal,
    )
    assert final == "Authorized Transformation"
    assert any(n.key == "llm_judge_capped_important_terms_list_add" for n in notes)


def test_merge_still_allows_critical_for_important_terms_list_add() -> None:
    proposal = _important_terms_proposal()
    llm = LLMReview(
        model="gpt-4o-mini",
        level=2,
        rde_class="Critical Distortion",
        notes=[],
    )
    final, _ = merge_rde_class(
        "Authorized Transformation",
        llm,
        proposal=proposal,
    )
    assert final == "Critical Distortion"


def test_merge_rde_takes_more_conservative_llm() -> None:
    llm = LLMReview(
        model="test",
        level=2,
        rde_class="Suspicious Drift",
        notes=[llm_text_note("llm note")],
    )
    final, notes = merge_rde_class("Inferred Extension", llm)
    assert final == "Suspicious Drift"
    assert any(n.key == "llm_judge_result" for n in notes)


def test_merge_rde_keeps_heuristic_when_stricter() -> None:
    llm = LLMReview(model="test", level=2, rde_class="Inferred Extension", notes=[])
    final, _ = merge_rde_class("Suspicious Drift", llm)
    assert final == "Suspicious Drift"
