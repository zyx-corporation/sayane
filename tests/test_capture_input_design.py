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


def test_important_terms_partial_yaml_section() -> None:
    text = """important_terms:
  - "柏崎刈羽原子力発電所"
  - "制度詩学"
  - "RDE"
"""
    config = BridgeConfig()
    candidate = create_from_capture(
        config,
        content=text,
        source_type="clipboard",
        raw_content=text,
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
            capture_confidence="high",
        ),
    )
    assert candidate.proposal.section == "important_terms"
    assert "persona:" not in (candidate.raw_capture or "")
    assert "preferred_name" not in (candidate.raw_capture or "")

    from sayane.bridge.candidate_api import _source_excerpt, get_candidate

    assert "important_terms" in _source_excerpt(candidate)
    detail = get_candidate(config, candidate.id)
    assert "important_terms" in detail["source_excerpt"]
    assert "preferred_name" not in detail["source_excerpt"]


def test_clipboard_fragment_preserves_exact_lines_in_raw_capture() -> None:
    path = Path(__file__).resolve().parents[1] / "docs" / "sample-context-chatgpt.yaml"
    lines = path.read_text(encoding="utf-8").splitlines()
    fragment = "\n".join(lines[320:334])
    assert "important_terms" in fragment
    assert "persona:" not in fragment.splitlines()[0]

    config = BridgeConfig()
    candidate = create_from_capture(
        config,
        content=fragment,
        source_type="clipboard",
        raw_content=fragment,
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
            capture_confidence="high",
        ),
    )
    assert candidate.proposal.section == "important_terms"
    assert candidate.raw_capture == fragment
    assert "柏崎刈羽原子力発電所" in (candidate.raw_capture or "")
    assert "ZAI統合アーキテクチャ" in (candidate.raw_capture or "")
    assert "preferred_name" not in (candidate.raw_capture or "")


def test_candidate_summary_preview_uses_raw_capture() -> None:
    from sayane.bridge.candidate_api import _capture_preview_text

    config = BridgeConfig()
    candidate = create_from_capture(
        config,
        content="ignored-for-preview",
        source_type="clipboard",
        raw_content="clipboard raw excerpt",
        capture_meta=CaptureMetadata(
            user_selected=True,
            capture_source="clipboard",
            capture_confidence="high",
        ),
    )
    assert "clipboard raw excerpt" in _capture_preview_text(candidate)
    assert "ignored-for-preview" not in _capture_preview_text(candidate)


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


def test_clipboard_full_persona_adds_warning() -> None:
    from sayane.bridge.capture_store import save_capture
    from sayane.bridge.models import CaptureRequest

    lines = ["persona:"] + [f"  field_{i}: value" for i in range(40)]
    content = "\n".join(lines)
    config = BridgeConfig()
    response = save_capture(
        config,
        CaptureRequest(
            content=content,
            source="clipboard",
            capture_source="clipboard",
            user_selected=True,
        ),
    )
    assert "full_persona_document_detected" in response.warnings


def test_clipboard_many_important_terms_adds_warning() -> None:
    from sayane.bridge.capture_store import save_capture
    from sayane.bridge.models import CaptureRequest

    text = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(encoding="utf-8")
    config = BridgeConfig()
    response = save_capture(
        config,
        CaptureRequest(
            content=text,
            source="clipboard",
            capture_source="clipboard",
            user_selected=True,
        ),
    )
    assert "clipboard_many_important_terms" in response.warnings


def test_clipboard_important_terms_only_has_no_full_persona_warning() -> None:
    from sayane.bridge.capture_store import save_capture
    from sayane.bridge.models import CaptureRequest

    content = "important_terms:\n  - \"RDE\"\n  - \"Sayane\""
    config = BridgeConfig()
    response = save_capture(
        config,
        CaptureRequest(
            content=content,
            source="clipboard",
            capture_source="clipboard",
            user_selected=True,
        ),
    )
    assert "full_persona_document_detected" not in response.warnings
