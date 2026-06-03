"""RDE summary message respects capture_source and warnings."""

from datetime import UTC, datetime

from sayane.core.candidate import (
    CandidateEvaluation,
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
    CaptureMetadata,
    UIBScores,
)
from sayane.evaluators.diff import profile_diff_for_candidate
from sayane.evaluators.rde_summary import (
    build_rde_summary_message,
    capture_source_from_meta,
    is_mixed_diff,
    should_mention_page_capture_noise,
)
from sayane.core.loader import load_profile
from pathlib import Path


def _candidate(
    *,
    capture_meta: CaptureMetadata,
    section: str = "mixed_sections",
) -> CandidateUpdate:
    proposal = CandidateProposal(
        section=section,
        operation="no_op_or_duplicate",
        add=[],
        items=[],
        already_present=[{"path": "core_concepts[].name", "name": "RDE"}],
        summary="mixed",
    )
    return CandidateUpdate(
        id="c1",
        status="evaluated",
        target_profile_id="default",
        content="body",
        source=CandidateSource(type=capture_meta.capture_source, captured_at=datetime.now(UTC)),
        proposal=proposal,
        capture_meta=capture_meta,
        evaluation=CandidateEvaluation(
            level=1,
            rde_class="Suspicious Drift",
            notes=[],
            uib=UIBScores(UD=0.5, MI=0.5, CH=0.5, DT=0.5, VP=0.5, FG=0.5),
            evaluated_at=datetime.now(UTC),
        ),
    )


def test_capture_source_selection_from_meta() -> None:
    meta = {"user_selected": True, "capture_source": "selection"}
    assert capture_source_from_meta(meta) == "selection"
    assert not should_mention_page_capture_noise(meta)


def test_capture_source_page_with_warnings() -> None:
    meta = {
        "capture_source": "page",
        "user_selected": False,
        "capture_warnings": ["page_capture_low_confidence", "ui_noise_detected"],
    }
    assert should_mention_page_capture_noise(meta)


def test_selection_mixed_no_page_capture_wording() -> None:
    meta = CaptureMetadata(
        user_selected=True,
        capture_source="selection",
        capture_confidence="high",
        requires_review=False,
        capture_warnings=[],
    )
    candidate = _candidate(capture_meta=meta)
    diff = {
        "section": "mixed_sections",
        "recommended_section": "review_required",
        "has_duplicates": True,
        "profile_update_recommended": False,
    }
    msg = build_rde_summary_message(candidate, diff)
    assert "選択範囲" in msg
    assert "ページ全体Capture" not in msg
    assert is_mixed_diff("mixed_sections", "review_required")


def test_page_mixed_mentions_page_capture() -> None:
    meta = CaptureMetadata(
        user_selected=False,
        capture_source="page",
        capture_confidence="low",
        requires_review=True,
        capture_warnings=["page_capture_low_confidence", "ui_noise_detected"],
    )
    candidate = _candidate(capture_meta=meta)
    diff = {
        "section": "mixed_sections",
        "recommended_section": "review_required",
        "has_duplicates": True,
        "profile_update_recommended": False,
    }
    msg = build_rde_summary_message(candidate, diff)
    assert "ページ全体Capture" in msg
    assert "選択範囲" not in msg


def test_selection_with_ui_noise_only_mentions_ui_not_page_body() -> None:
    meta = CaptureMetadata(
        user_selected=True,
        capture_source="selection",
        capture_warnings=["ui_noise_detected"],
    )
    assert should_mention_page_capture_noise(meta.model_dump())


def test_diff_api_includes_aligned_summary() -> None:
    profile = load_profile(Path("examples/profiles/minimal.yaml"))
    meta = CaptureMetadata(
        user_selected=True,
        capture_source="selection",
        capture_warnings=[],
    )
    candidate = _candidate(capture_meta=meta)
    diff = profile_diff_for_candidate(profile, candidate)
    assert diff["section"] == "mixed_sections"
    assert "ページ全体Capture" not in diff["rde_summary_message"]
    assert "選択範囲" in diff["rde_summary_message"]
