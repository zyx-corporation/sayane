"""Section inference rules for structured page capture."""

from pathlib import Path

from sayane.core.loader import load_profile
from sayane.core.models import CanonicalTerm, Knowledge, MajorProject, Organization
from sayane.evaluators.capture_classify import (
    CORE_CONCEPT_PATH,
    ORGANIZATION_PATH,
    classify_structured_capture,
)


def _profile() -> object:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.knowledge = Knowledge(concepts=["RDE", "ΔM", "制度詩学", "Resonanceverse"])
    profile.organization = Organization(name="ZYX Corp株式会社")
    profile.major_projects = [
        MajorProject(name="Sayane", summary="tool"),
        MajorProject(name="Kotone", summary="edge"),
    ]
    profile.canonical_terms = [
        CanonicalTerm(term="RDE", expansion="Resonant Deviation Evaluator"),
    ]
    return profile


def test_organization_not_identity_for_corp() -> None:
    profile = _profile()
    content = """
major_projects:
  - name: "ZYX Corp株式会社"
    summary: "client"
"""
    result = classify_structured_capture(content, profile)
    assert result is not None
    assert not result.items
    assert len(result.already_present) == 1
    assert result.already_present[0]["path"] == ORGANIZATION_PATH


def test_core_concepts_not_major_projects() -> None:
    profile = _profile()
    content = """
major_projects:
  - name: "ΔM"
    summary: "drift"
  - name: "制度詩学"
    summary: "poetics"
"""
    result = classify_structured_capture(content, profile)
    assert result is not None
    assert not result.items
    for entry in result.already_present:
        assert entry["path"] == CORE_CONCEPT_PATH
        assert "major_projects" not in entry["path"]


def test_kotomi_is_new_major_project() -> None:
    profile = _profile()
    content = """
major_projects:
  - name: "Kotomi"
    summary: "new"
"""
    result = classify_structured_capture(content, profile)
    assert result is not None
    kotomi = [i for i in result.items if i.name == "Kotomi"]
    assert kotomi and kotomi[0].section == "major_projects"
