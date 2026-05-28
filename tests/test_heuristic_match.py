"""Regression tests for bounded Level-1 heuristic matching."""

import pytest

from sayane.core.candidate import CandidateProposal
from sayane.evaluators.heuristic_match import (
    contains_dot_path,
    contains_phrase,
    contains_word,
    has_core_values_phrase,
    has_imperative_always,
    has_imperative_never,
    has_yaml_key,
)
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.evaluators.sections import infer_proposal_section
from sayane.evaluators.uib import score_uib

# --- Known false positives (must NOT match) ---

_SECTION_FALSE_POSITIVES = [
    ("- Melotone: Edge AI", "knowledge.concepts"),
    ("secretary@corp.com", "knowledge.concepts"),
    ("private keyboard layout", "knowledge.concepts"),
    ("unavoidable trade-off", "knowledge.concepts"),
    ("preference: strong", "knowledge.concepts"),
    ("hardcore values in gaming", "knowledge.concepts"),
    ("microservices roles model", "knowledge.concepts"),
    ("discussing voice.tonal analysis", "knowledge.concepts"),
]

_RDE_FALSE_POSITIVES = [
    "secretary@corp.com",
    "The secret garden is beautiful.",
    "private keyboard shortcuts",
    "hardcore values only",
    "OpenExample governance overview",
    "top-secret clearance document",
]

_UIB_URL_NO_FALSE_UNCERTAINTY = "https://example.com/path?foo=bar&baz=1"


@pytest.mark.parametrize(("content", "expected"), _SECTION_FALSE_POSITIVES)
def test_section_inference_avoids_substring_false_positives(
    content: str,
    expected: str,
) -> None:
    assert infer_proposal_section(content) == expected


@pytest.mark.parametrize("content", _RDE_FALSE_POSITIVES)
def test_rde_avoids_substring_false_positives(content: str) -> None:
    proposal = CandidateProposal(section="knowledge.concepts", add=["item"])
    rde_class, _ = classify_rde(content, proposal)
    assert rde_class not in ("Critical Distortion", "Suspicious Drift")


def test_rde_still_detects_real_secrets() -> None:
    proposal = CandidateProposal(section="knowledge.concepts", add=["leak"])
    content = "Here is my api key: sk-live-abcdef"
    rde_class, _ = classify_rde(content, proposal)
    assert rde_class in ("Suspicious Drift", "Critical Distortion")


def test_uib_does_not_treat_url_query_as_uncertainty() -> None:
    proposal = build_proposal_from_content("Stable factual statement about design.")
    scores = score_uib(_UIB_URL_NO_FALSE_UNCERTAINTY, proposal)
    assert scores.UD == 0.55


def test_yaml_key_helpers() -> None:
    assert has_yaml_key("tone:\n  - calm", "tone")
    assert not has_yaml_key("Melotone: Edge AI", "tone")
    assert contains_dot_path("set values.core item", "values.core")
    assert not contains_dot_path("hardcore values", "values.core")
    assert has_core_values_phrase("Our core values include dignity.")
    assert not has_core_values_phrase("hardcore values")


def test_imperative_helpers() -> None:
    assert has_imperative_always("You should always check twice.")
    assert not has_imperative_always("always-on monitoring")
    assert has_imperative_never("Never share passwords.")
    assert not has_imperative_never("nevertheless continue")


def test_word_and_phrase_boundaries() -> None:
    assert contains_word("top-secret", "secret") is False
    assert contains_word("my secret plan", "secret")
    assert contains_phrase("here is my api key", "api key")
    proposal = CandidateProposal(section="knowledge.concepts", add=["x"])
    assert classify_rde("The secret garden is beautiful.", proposal)[0] == "Inferred Extension"


def test_persona_proposal_skips_markdown_headers() -> None:
    content = (
        "# Persona\n"
        "person:\n"
        "  name:\n"
        "    formal_ja: Example\n"
        "projects:\n"
        "  sample:\n"
        "    note: demo\n"
        "- First real bullet about RDE.\n"
        "- Second bullet about portability.\n"
    )
    proposal = build_proposal_from_content(content)
    assert proposal.section == "knowledge.concepts"
    assert not any(item.startswith("#") for item in proposal.add)
    assert any("RDE" in item or "bullet" in item for item in proposal.add)


def test_structured_persona_yaml() -> None:
    content = (
        "person:\n  name:\n    formal_ja: Example\n"
        "projects:\n  melotone:\n    name_en: Melotone\n"
        "organization:\n  roles:\n    - lead\n"
    )
    assert infer_proposal_section(content) == "knowledge.concepts"
