from sayane.core.candidate import LLMReview
from sayane.evaluators.rde_merge import merge_rde_class


def test_merge_rde_takes_more_conservative_llm() -> None:
    llm = LLMReview(model="test", level=2, rde_class="Suspicious Drift", notes=["llm note"])
    final, notes = merge_rde_class("Inferred Extension", llm)
    assert final == "Suspicious Drift"
    assert any("llm" in n.lower() for n in notes)


def test_merge_rde_keeps_heuristic_when_stricter() -> None:
    llm = LLMReview(model="test", level=2, rde_class="Inferred Extension", notes=[])
    final, _ = merge_rde_class("Suspicious Drift", llm)
    assert final == "Suspicious Drift"
