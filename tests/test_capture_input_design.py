"""Input design: selection/clipboard capture, YAML parse failures, persona classification."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import (
    CaptureMetadata,
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
)
from sayane.core.loader import load_profile
from sayane.core.models import Knowledge, MajorProject, Organization
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.storage.candidates import create_from_capture


def _profile_with_persona_fields() -> object:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    profile.identity.name = "Tomoyuki Kano"
    profile.identity.preferred_name = "tomyuk"
    profile.organization = Organization(name="ZYX Corp株式会社")
    profile.knowledge = Knowledge(concepts=["Python", "RDE"])
    profile.major_projects = [MajorProject(name="Sayane", summary="context tool")]
    return profile


PERSONA_YAML = """\
persona:
  preferred_name: "tomyuk"
  casual_name: "ともゆきさん"
  formal_name: "Tomoyuki Kano"
  external_japanese_name: "加納 智之"
  email: "tomyuk@zyxcorp.jp"
  role:
    - "AI関連スタートアップ経営者"
    - "エンジニア"
    - "アーキテクト"
"""

BROKEN_YAML = """\
values:
  core:
    - "元議論より強い主張へのすり替え"  development_preferences:
      languages: ["Python"]
"""


def test_clipboard_capture_sets_capture_source() -> None:
    config = BridgeConfig()
    candidate = create_from_capture(
        config,
        content="clipboard note",
        source_type="clipboard",
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
            capture_confidence="high",
        ),
    )
    assert candidate.capture_meta is not None
    assert candidate.capture_meta.capture_source == "clipboard"
    assert candidate.raw_capture == "clipboard note"
    assert candidate.cleaned_capture == "clipboard note"


def test_selection_capture_sets_capture_source_and_raw() -> None:
    config = BridgeConfig()
    candidate = create_from_capture(
        config,
        content=PERSONA_YAML,
        source_type="selection",
        raw_content=PERSONA_YAML,
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="selection",
            capture_confidence="high",
        ),
    )
    assert candidate.capture_meta is not None
    assert candidate.capture_meta.capture_source == "selection"
    assert candidate.raw_capture == PERSONA_YAML
    assert candidate.cleaned_capture == PERSONA_YAML.strip()


def test_broken_yaml_parse_failed_not_major_projects() -> None:
    meta = CaptureMetadata(user_selected=True, capture_source="selection")
    proposal = build_proposal_from_content(BROKEN_YAML, profile=_profile_with_persona_fields(), capture_meta=meta)
    assert proposal.section == "review_required"
    assert proposal.operation == "parse_failed"
    assert proposal.section != "major_projects"
    assert proposal.parse_error or proposal.summary


def test_broken_yaml_diff_review_required() -> None:
    meta = CaptureMetadata(user_selected=True, capture_source="selection")
    proposal = build_proposal_from_content(BROKEN_YAML, capture_meta=meta)
    candidate = CandidateUpdate(
        id="broken",
        status="pending",
        target_profile_id="default",
        content=BROKEN_YAML,
        raw_capture=BROKEN_YAML,
        cleaned_capture=BROKEN_YAML,
        capture_meta=meta,
        source=CandidateSource(type="selection", captured_at=datetime.now(UTC)),
        proposal=proposal,
    )
    diff = profile_diff_for_candidate(_profile_with_persona_fields(), candidate)
    assert diff["section"] == "review_required"
    assert diff["recommended_section"] == "review_required"
    assert diff["profile_update_recommended"] is False
    assert diff.get("parse_error")


def test_persona_root_not_major_projects() -> None:
    profile = _profile_with_persona_fields()
    meta = CaptureMetadata(user_selected=True, capture_source="selection")
    proposal = build_proposal_from_content(PERSONA_YAML, profile=profile, capture_meta=meta)
    assert proposal.section != "major_projects"
    assert proposal.section in {"persona", "mixed_sections", "review_required"}


def test_persona_already_present_detected() -> None:
    profile = _profile_with_persona_fields()
    meta = CaptureMetadata(user_selected=True, capture_source="selection")
    proposal = build_proposal_from_content(PERSONA_YAML, profile=profile, capture_meta=meta)
    names = {e.get("name", "").casefold() for e in proposal.already_present}
    assert "tomyuk" in names or "tomoyuki kano" in names


def test_no_op_unknown_section_not_major_projects() -> None:
    meta = CaptureMetadata(user_selected=True, capture_source="selection")
    proposal = build_proposal_from_content("   \n  ", capture_meta=meta)
    if proposal.operation == "no_op_or_duplicate" and not proposal.items:
        assert proposal.section != "major_projects"


def test_no_effective_proposal_review_required() -> None:
    proposal = CandidateProposal(
        section="major_projects",
        operation="no_op_or_duplicate",
        add=[],
        items=[],
        already_present=[],
    )
    from sayane.evaluators.capture_parse import build_no_effective_proposal

    fixed = build_no_effective_proposal("empty")
    assert fixed.section == "review_required"
    assert fixed.operation == "parse_failed_or_no_effective_update"


def test_raw_capture_matches_content_for_selection() -> None:
    config = BridgeConfig()
    text = PERSONA_YAML
    candidate = create_from_capture(
        config,
        content=text,
        source_type="selection",
        raw_content=text,
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="selection",
        ),
    )
    assert candidate.raw_capture == text
    assert candidate.content == text.strip()
    assert "preferred_name" in (candidate.raw_capture or "")


@pytest.mark.parametrize(
    ("capture_source", "user_selected"),
    [
        ("clipboard", True),
        ("selection", True),
    ],
)
def test_user_explicit_capture_sources(capture_source: str, user_selected: bool) -> None:
    meta = CaptureMetadata(
        user_selected=user_selected,
        capture_source=capture_source,  # type: ignore[arg-type]
    )
    assert meta.capture_source == capture_source
