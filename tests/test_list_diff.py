"""Tests for list-section diff (important_terms)."""

from __future__ import annotations

from pathlib import Path

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CaptureMetadata, CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.loader import load_profile
from sayane.core.models import Knowledge, MajorProject, Organization
from sayane.evaluators.capture_parse import classify_important_terms_yaml, try_parse_yaml
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.list_diff import diff_string_list
from sayane.evaluators.rde import classify_rde
from sayane.storage.candidates import create_from_capture

EXISTING = [
    "柏崎刈羽原子力発電所",
    "制度詩学",
    "RDE",
    "RDE vNext",
    "T-RDE",
    "ΔM",
    "制度的シコファンシー",
    "Kotone",
    "Kotonoha",
    "Sayane",
    "Awai Commons",
]


def _profile_with_terms() -> object:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.identity.name = "Tomoyuki Kano"
    profile.organization = Organization(name="ZYX Corp株式会社")
    terms = [
        "柏崎刈羽原子力発電所",
        "制度詩学",
        "RDE",
        "RDE vNext",
        "T-RDE",
        "ΔM",
        "制度的シコファンシー",
        "Kotone",
        "Kotonoha",
        "Sayane",
        "Awai Commons",
    ]
    profile.important_terms = list(terms)
    profile.knowledge = Knowledge(concepts=list(terms))
    profile.major_projects = [MajorProject(name="Sayane", summary="context tool")]
    return profile


def test_diff_string_list_only_added() -> None:
    proposed = [*EXISTING, "Context-Aware Harness", "ZAI統合アーキテクチャ"]
    diff = diff_string_list(EXISTING, proposed)
    assert diff.added == ["Context-Aware Harness", "ZAI統合アーキテクチャ"]
    assert diff.removed == []
    assert len(diff.unchanged) == 11


def test_important_terms_diff_api() -> None:
    content = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(
        encoding="utf-8",
    )
    parsed, _ = try_parse_yaml(content)
    assert isinstance(parsed, dict)
    profile = _profile_with_terms()
    proposal = classify_important_terms_yaml(parsed, profile)
    candidate = CandidateUpdate(
        id="test-id",
        target_profile_id="default",
        content=content,
        raw_capture=content,
        source=CandidateSource(type="clipboard", uri=None, captured_at=__import__("datetime").datetime.now(__import__("datetime").UTC)),
        proposal=proposal,
    )
    diff = profile_diff_for_candidate(profile, candidate)
    assert "note" not in diff or "not automated" not in str(diff.get("note", ""))
    list_diff = diff["list_diff"]
    assert list_diff["operation"] == "list_add"
    assert list_diff["added"] == ["Context-Aware Harness", "ZAI統合アーキテクチャ"]
    assert list_diff["unchanged_count"] == 11
    assert len(diff["add"]) == 2


def test_important_terms_small_additions_not_suspicious_drift() -> None:
    parsed, _ = try_parse_yaml(
        "important_terms:\n  - \"RDE\"\n  - \"Sayane\"\n  - \"Context-Aware Harness\"\n",
    )
    assert isinstance(parsed, dict)
    proposal = classify_important_terms_yaml(parsed, _profile_with_terms())
    rde, _notes = classify_rde("important_terms:\n  - RDE\n  - Sayane\n", proposal)
    assert rde != "Suspicious Drift"
    assert rde != "Critical Distortion"
    assert len(proposal.items) == 1
    assert proposal.items[0]["name"] == "Context-Aware Harness"


def test_important_terms_merge_appends_only_added_terms() -> None:
    parsed, _ = try_parse_yaml(
        "important_terms:\n"
        '  - "RDE"\n'
        '  - "Sayane"\n'
        '  - "Context-Aware Harness"\n',
    )
    assert isinstance(parsed, dict)
    profile = _profile_with_terms()
    profile.important_terms = ["RDE", "Sayane"]
    proposal = classify_important_terms_yaml(parsed, profile)
    candidate = CandidateUpdate(
        id="merge-test",
        target_profile_id="default",
        content="",
        source=CandidateSource(
            type="clipboard",
            uri=None,
            captured_at=__import__("datetime").datetime.now(__import__("datetime").UTC),
        ),
        proposal=proposal,
    )
    from sayane.evaluators.merge import merge_candidate_into_profile

    merge_candidate_into_profile(profile, candidate)
    assert profile.important_terms == [
        "RDE",
        "Sayane",
        "Context-Aware Harness",
    ]


def test_important_terms_approve_merges_to_profile_important_terms(tmp_path) -> None:
    import shutil

    from sayane.evaluators.service import approve_candidate, evaluate_candidate

    content = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(
        encoding="utf-8",
    )
    home = tmp_path / "sayane"
    config = BridgeConfig(home=home)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    candidate = create_from_capture(
        config,
        content=content,
        source_type="clipboard",
        profile_id="default",
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
        ),
    )
    evaluate_candidate(config, candidate.id, level=1)
    approved = approve_candidate(config, candidate.id)
    assert approved.status == "approved"
    profile = load_profile(profile_dir / "sayane.profile.yaml")
    assert "Context-Aware Harness" in profile.important_terms
    assert "ZAI統合アーキテクチャ" in profile.important_terms
    assert profile.important_terms.count("RDE") <= 1
    assert profile.important_terms.count("Sayane") <= 1


def test_important_terms_partial_capture_all_unchanged() -> None:
    fragment = """important_terms:
  - "柏崎刈羽原子力発電所"
  - "制度詩学"
  - "RDE"
  - "RDE vNext"
  - "T-RDE"
  - "ΔM"
"""
    parsed, _ = try_parse_yaml(fragment)
    assert isinstance(parsed, dict)
    proposal = classify_important_terms_yaml(parsed, _profile_with_terms())
    assert proposal.operation == "no_op_or_duplicate"
    assert proposal.items == []
    assert len(proposal.already_present) == 6


def test_important_terms_sayane_add_when_only_in_major_projects() -> None:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.important_terms = ["RDE"]
    profile.major_projects = [MajorProject(name="Sayane", summary="context tool")]
    parsed, _ = try_parse_yaml('important_terms:\n  - "Sayane"\n')
    assert isinstance(parsed, dict)
    proposal = classify_important_terms_yaml(parsed, profile)
    assert len(proposal.items) == 1
    assert proposal.items[0]["name"] == "Sayane"
    assert proposal.already_present == []


def test_important_terms_display_summary_ja() -> None:
    from sayane.evaluators.list_diff import important_terms_display_summary

    content = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(
        encoding="utf-8",
    )
    parsed, _ = try_parse_yaml(content)
    assert isinstance(parsed, dict)
    proposal = classify_important_terms_yaml(parsed, _profile_with_terms())
    preview = important_terms_display_summary(proposal, locale="ja")
    assert "2 件の追加候補" in preview
    assert "Context-Aware Harness" in preview
    assert "柏崎刈羽原子力発電所" not in preview
