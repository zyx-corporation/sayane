"""Candidate Update file storage."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from omomuki.bridge.config import BridgeConfig
from omomuki.core.candidate import (
    CandidateProposal,
    CandidateSource,
    CandidateUpdate,
)


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
        source=CandidateSource(
            type=data.get("source") or "capture",
            uri=data.get("source_url"),
            captured_at=ts,
        ),
        proposal=CandidateProposal(section="knowledge.concepts", add=[], summary=None),
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
    _candidates_dir(config).mkdir(parents=True, exist_ok=True)
    path = _candidate_path(config, candidate.id)
    path.write_text(
        json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False, indent=2),
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
) -> CandidateUpdate:
    from omomuki.evaluators.proposal import build_proposal_from_content

    now = datetime.now(UTC)
    candidate_id = uuid4().hex
    proposal = build_proposal_from_content(content)
    candidate = CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content=content,
        source=CandidateSource(type=source_type, uri=source_url, captured_at=now),
        proposal=proposal,
    )
    save_candidate(config, candidate)
    return candidate
