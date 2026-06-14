"""Candidate Update file storage."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import (
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
    CaptureMetadata,
)
from sayane.storage.security_policy import require_local_working_store


def _candidates_dir(config: BridgeConfig) -> Path:
    return config.candidates_dir


def _candidate_path(config: BridgeConfig, candidate_id: str) -> Path:
    return _candidates_dir(config) / f"{candidate_id}.json"


def from_legacy_capture(data: dict) -> CandidateUpdate:
    """Upgrade Phase 2 capture JSON to CandidateUpdate."""
    captured_at = data.get("captured_at")
    if isinstance(captured_at, str):
        ts = datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    else:
        ts = datetime.now(UTC)
    content = data.get("content", "")
    return CandidateUpdate(
        id=data.get("id", uuid4().hex),
        status="pending",
        target_profile_id="default",
        content=content,
        raw_capture=content,
        cleaned_capture=content,
        display_summary=content[:120] if content else None,
        source=CandidateSource(
            type=data.get("source") or "capture",
            uri=data.get("source_url"),
            captured_at=ts,
        ),
        proposal=CandidateProposal(
            section="knowledge.concepts",
            add=[],
            summary=None,
        ),
    )


def load_candidate(config: BridgeConfig, candidate_id: str) -> CandidateUpdate:
    path = _candidate_path(config, candidate_id)
    if not path.exists():
        raise FileNotFoundError(f"Candidate not found: {candidate_id}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") == "CandidateUpdate":
        return CandidateUpdate.model_validate(data)
    return from_legacy_capture(data)


def save_candidate(config: BridgeConfig, candidate: CandidateUpdate) -> Path:
    path = _candidate_path(config, candidate.id)
    require_local_working_store(path, record_class="candidate")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            candidate.model_dump(mode="json"),
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return path


def list_candidate_ids(config: BridgeConfig) -> list[str]:
    directory = _candidates_dir(config)
    if not directory.exists():
        return []
    return sorted(path.stem for path in directory.glob("*.json"))


def create_from_capture(
    config: BridgeConfig,
    content: str,
    source_type: str,
    source_url: str | None = None,
    *,
    section: str | None = None,
    profile_id: str = "default",
    locale: str | None = None,
    raw_content: str | None = None,
    capture_meta: CaptureMetadata | None = None,
    display_summary: str | None = None,
) -> CandidateUpdate:
    from sayane.evaluators.capture_cleaning import (
        clean_capture_text,
        display_summary_from_text,
    )
    from sayane.evaluators.list_diff import important_terms_display_summary
    from sayane.evaluators.proposal import build_proposal_from_content
    from sayane.evaluators.sections import normalize_proposal_section
    from sayane.storage.factory import open_storage

    now = datetime.now(UTC)
    candidate_id = uuid4().hex
    target_section = normalize_proposal_section(section) if section else None
    try:
        profile_bundle = open_storage(home=config.home, profile=None, profile_id=profile_id)
        profile = profile_bundle.profile.load()
    except Exception:
        profile = None

    raw = raw_content if raw_content is not None else content
    user_explicit = capture_meta is not None and capture_meta.capture_source in (
        "selection",
        "clipboard",
    )
    if user_explicit:
        cleaned = content.strip()
        ui_noise = False
    else:
        cleaned, ui_noise = clean_capture_text(content)
    if capture_meta is None:
        capture_meta = CaptureMetadata()
    warnings = list(capture_meta.capture_warnings)
    if ui_noise and "ui_noise_detected" not in warnings:
        warnings.append("ui_noise_detected")
    capture_meta = capture_meta.model_copy(update={"capture_warnings": warnings})

    proposal = build_proposal_from_content(
        cleaned,
        section=target_section,
        profile=profile,
        capture_meta=capture_meta,
    )
    if proposal.parse_error:
        capture_meta = capture_meta.model_copy(update={"parse_error": proposal.parse_error})
    requires_review = capture_meta.requires_review or proposal.section == "review_required"
    if requires_review and not capture_meta.requires_review:
        capture_meta = capture_meta.model_copy(update={"requires_review": True})
    summary = display_summary or proposal.summary or display_summary_from_text(cleaned)
    if proposal.section == "important_terms" and not display_summary:
        summary = important_terms_display_summary(proposal, locale=locale)
    candidate = CandidateUpdate(
        id=candidate_id,
        status="pending",
        locale=locale,
        target_profile_id=profile_id,
        content=cleaned,
        raw_capture=raw,
        cleaned_capture=cleaned,
        display_summary=summary,
        capture_meta=capture_meta,
        generator_id="sayane.capture",
        source=CandidateSource(
            type=source_type,
            uri=source_url,
            captured_at=now,
        ),
        proposal=proposal,
    )
    save_candidate(config, candidate)
    return candidate
