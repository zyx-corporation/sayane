from sayane.core.candidate import CandidateProposal
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.evaluators.uib import score_uib


def test_rde_inferred_extension_for_knowledge() -> None:
    content = "Sayane provides context portability across LLM platforms."
    proposal = build_proposal_from_content(content)
    rde_class, _ = classify_rde(content, proposal)
    assert rde_class == "Inferred Extension"


def test_rde_unresolved_gap_short_content() -> None:
    proposal = CandidateProposal(section="knowledge.concepts", add=[])
    rde_class, _ = classify_rde("short", proposal)
    assert rde_class == "Unresolved Gap"


def test_rde_critical_for_secrets() -> None:
    content = "Here is my api key: sk-secret-12345"
    proposal = build_proposal_from_content(content)
    rde_class, _ = classify_rde(content, proposal)
    assert rde_class in ("Suspicious Drift", "Critical Distortion")


def test_uib_scores_in_range() -> None:
    proposal = build_proposal_from_content("Some captured text with maybe uncertainty.")
    scores = score_uib("Some captured text with maybe uncertainty.", proposal)
    for field in ("UD", "MI", "CH", "DT", "VP", "FG"):
        value = getattr(scores, field)
        assert 0.0 <= value <= 1.0
