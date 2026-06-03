"""Capture cleaning, classification, and diff recommendation alignment."""

from pathlib import Path

from sayane.core.candidate import CaptureMetadata, CandidateProposal
from sayane.core.loader import load_profile
from sayane.core.models import CanonicalTerm, Knowledge, MajorProject, Organization
from sayane.evaluators.capture_cleaning import clean_capture_text, is_ui_noise_line
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.rde import classify_rde
from sayane.core.candidate import CandidateSource, CandidateUpdate
from datetime import UTC, datetime


def _profile_with_concepts() -> object:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.knowledge = Knowledge(concepts=["RDE", "ΔM", "制度詩学", "Resonanceverse"])
    profile.organization = Organization(name="ZYX Corp株式会社")
    profile.major_projects = [
        MajorProject(name="Sayane", summary="local-first context tool"),
        MajorProject(name="Kotone", summary="edge AI"),
    ]
    profile.canonical_terms = [
        CanonicalTerm(term="RDE", expansion="Resonant Deviation Evaluator"),
    ]
    profile.identity.name = "Example User"
    return profile


def test_ui_noise_lines_removed() -> None:
    raw = "\n".join(
        [
            "チャット履歴",
            "新しいチャット",
            "Sayane is a local-first tool.",
            "1Passwordメニューが利用できます",
        ],
    )
    cleaned, detected = clean_capture_text(raw)
    assert "チャット履歴" not in cleaned
    assert "新しいチャット" not in cleaned
    assert "1Password" not in cleaned
    assert "Sayane is a local-first tool." in cleaned
    assert detected is True
    assert is_ui_noise_line("チャット履歴")


def test_page_capture_low_confidence_mixed_sections() -> None:
    profile = _profile_with_concepts()
    content = """
major_projects:
  - name: "ZYX Corp株式会社"
    summary: "client org"
  - name: "RDE"
    summary: "evaluator framework"
  - name: "ΔM"
    summary: "semantic drift"
  - name: "制度詩学"
    summary: "poetics"
  - name: "Resonanceverse"
    summary: "world"
"""
    meta = CaptureMetadata(
        user_selected=False,
        capture_source="page",
        capture_confidence="low",
        requires_review=True,
        capture_warnings=["page_capture_low_confidence", "ui_noise_detected"],
    )
    proposal = build_proposal_from_content(
        content,
        profile=profile,
        capture_meta=meta,
    )
    assert proposal.section == "mixed_sections"
    assert proposal.operation == "no_op_or_duplicate"
    assert not proposal.items
    assert proposal.summary == "Structured capture: 0 new, 5 already in profile"
    assert len(proposal.already_present) == 5
    by_name = {e["name"]: e["path"] for e in proposal.already_present}
    assert by_name["ZYX Corp株式会社"] == "organization.name"
    assert by_name["RDE"] == "core_concepts[].name"
    assert by_name["ΔM"] == "core_concepts[].name"
    assert by_name["制度詩学"] == "core_concepts[].name"
    assert by_name["Resonanceverse"] == "core_concepts[].name"


def test_core_concepts_not_in_major_projects_add() -> None:
    profile = _profile_with_concepts()
    content = """
major_projects:
  - name: "RDE"
    summary: "should not be a project"
"""
    proposal = build_proposal_from_content(content, profile=profile)
    assert proposal.section in {"mixed_sections", "knowledge.concepts"}
    if proposal.section == "major_projects":
        assert not any(i.get("name") == "RDE" for i in proposal.items)


def test_diff_suspicious_drift_not_recommended() -> None:
    profile = _profile_with_concepts()
    proposal = CandidateProposal(
        section="mixed_sections",
        operation="no_op_or_duplicate",
        add=[],
        items=[],
        already_present=[{"path": "knowledge.concepts", "name": "RDE"}],
        summary="mixed",
    )
    candidate = CandidateUpdate(
        id="abc",
        status="evaluated",
        target_profile_id="default",
        content="cleaned",
        cleaned_capture="cleaned",
        display_summary="mixed capture",
        capture_meta=CaptureMetadata(capture_confidence="low", requires_review=True),
        source=CandidateSource(type="page", captured_at=datetime.now(UTC)),
        proposal=proposal,
        evaluation=None,
    )
    rde_class, _ = classify_rde("x" * 40, proposal)
    from sayane.core.candidate import CandidateEvaluation, UIBScores

    candidate.evaluation = CandidateEvaluation(
        level=1,
        rde_class=rde_class,
        notes=[],
        uib=UIBScores(UD=0.5, MI=0.5, CH=0.5, DT=0.5, VP=0.5, FG=0.5),
        evaluated_at=datetime.now(UTC),
    )
    diff = profile_diff_for_candidate(profile, candidate)
    assert diff["recommended_section"] == "review_required"
    assert diff["has_duplicates"] is True
    assert diff["profile_update_recommended"] is False
    assert "ページ全体Capture" in diff.get("rde_summary_message", "")


def test_display_summary_not_full_page() -> None:
    long_body = "word " * 500
    meta = CaptureMetadata(capture_confidence="low")
    proposal = build_proposal_from_content(long_body, capture_meta=meta)
    assert proposal.summary is not None
    assert len(proposal.summary) < len(long_body)


def test_selection_capture_high_confidence_allows_items() -> None:
    profile = _profile_with_concepts()
    content = "- NewConceptAlpha\n"
    meta = CaptureMetadata(
        user_selected=True,
        capture_confidence="high",
        requires_review=False,
    )
    proposal = build_proposal_from_content(
        content,
        profile=profile,
        capture_meta=meta,
    )
    assert proposal.section == "knowledge.concepts"
    assert proposal.add or proposal.items or proposal.operation
