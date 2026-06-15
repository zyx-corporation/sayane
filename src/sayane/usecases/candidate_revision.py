"""Candidate revision creation and lineage recording."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateSource, CandidateUpdate
from sayane.evaluators.proposal import build_proposal_from_content
from sayane.evaluators.sections import normalize_proposal_section
from sayane.lineage.record import record_lineage_event
from sayane.storage.candidates import load_candidate, save_candidate


def revise_candidate_for_api(
    config: BridgeConfig,
    candidate_id: str,
    *,
    edited_text: str,
    target_section: str | None = None,
    change_reason: str | None = None,
) -> dict[str, Any]:
    """Create a revised Candidate from an existing one (#119)."""
    original = load_candidate(config, candidate_id)
    proposal = build_proposal_from_content(
        edited_text,
        section=(
            normalize_proposal_section(target_section)
            if target_section
            else None
        ),
    )
    revised = CandidateUpdate(
        id=uuid4().hex,
        status="pending",
        locale=original.locale,
        target_profile_id=original.target_profile_id,
        content=edited_text,
        raw_capture=edited_text,
        cleaned_capture=edited_text,
        display_summary=f"Revised from {candidate_id[:8]}: {edited_text[:120]}",
        capture_meta=original.capture_meta,
        source=CandidateSource(
            type="candidate_revision",
            uri=original.source.uri,
            captured_at=datetime.now(UTC),
        ),
        proposal=proposal,
        storage_policy=original.storage_policy,
        parent_capture_id=original.parent_capture_id or original.id,
        generator_id="sayane.candidate_revision",
    )
    save_candidate(config, revised)
    source_kind = (
        original.capture_meta.capture_source if original.capture_meta else None
    )
    meta: dict[str, Any] = {
        "source_candidate_id": candidate_id,
        "revised_candidate_id": revised.id,
        "operation": "user_revision",
    }
    if change_reason:
        meta["change_reason"] = change_reason
    record_lineage_event(
        config,
        original.target_profile_id,
        operation="candidate_revised",
        node_kind="candidate",
        actor="user",
        capture_id=original.id,
        candidate_id=revised.id,
        context_path=target_section or original.proposal.section,
        source_url=original.source.uri,
        source_kind=source_kind,
        note=change_reason,
        metadata=meta,
    )
    return revised.model_dump(mode="json")
