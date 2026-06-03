"""All structured capture lines already present in profile."""

from pathlib import Path

from sayane.core.candidate import CaptureMetadata
from sayane.core.loader import load_profile
from sayane.core.models import CanonicalTerm, Knowledge, MajorProject, Organization
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.core.candidate import CandidateSource, CandidateUpdate
from datetime import UTC, datetime


def _profile_five_existing() -> object:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.knowledge = Knowledge(concepts=["RDE", "ΔM", "制度詩学", "Resonanceverse"])
    profile.organization = Organization(name="ZYX Corp株式会社")
    profile.major_projects = [
        MajorProject(name="Sayane", summary="tool"),
    ]
    profile.canonical_terms = [
        CanonicalTerm(term="RDE", expansion="Resonant Deviation Evaluator"),
    ]
    profile.identity.name = "Example User"
    return profile


def test_mixed_sections_all_already_present() -> None:
    profile = _profile_five_existing()
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
        capture_warnings=["page_capture_low_confidence"],
    )
    proposal = build_proposal_from_content(content, profile=profile, capture_meta=meta)
    assert proposal.section == "mixed_sections"
    assert proposal.operation == "no_op_or_duplicate"
    assert proposal.add == []
    assert not proposal.items
    assert proposal.summary == "Structured capture: 0 new, 5 already in profile"
    assert len(proposal.already_present) == 5
    by_name = {e["name"]: e["path"] for e in proposal.already_present}
    assert by_name["ZYX Corp株式会社"] == "organization.name"
    assert by_name["RDE"] == "core_concepts[].name"
    assert by_name["ΔM"] == "core_concepts[].name"
    assert by_name["制度詩学"] == "core_concepts[].name"
    assert by_name["Resonanceverse"] == "core_concepts[].name"

    candidate = CandidateUpdate(
        id="x",
        status="evaluated",
        target_profile_id="default",
        content="c",
        source=CandidateSource(type="page", captured_at=datetime.now(UTC)),
        proposal=proposal,
        evaluation=None,
    )
    diff = profile_diff_for_candidate(profile, candidate)
    assert diff["section"] == "mixed_sections"
    assert diff["recommended_section"] == "review_required"
    assert diff["add"] == []
    assert diff["has_duplicates"] is True
    assert diff["profile_update_recommended"] is False
