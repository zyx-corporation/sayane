"""Bridge handlers for Candidate evaluate / approve flow."""

from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.core.candidate import CandidateUpdate
from sayane.evaluators.service import (
    approve_candidate,
    diff_candidate,
    evaluate_candidate,
    reject_candidate,
)
from sayane.storage.candidates import list_candidate_ids, load_candidate


def list_candidates(config: BridgeConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for cid in list_candidate_ids(config):
        try:
            c = load_candidate(config, cid)
            items.append(_candidate_summary(c))
        except Exception:
            continue
    return items


def get_candidate(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    return load_candidate(config, candidate_id).model_dump(mode="json")


def post_evaluate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    level: int = 1,
) -> dict[str, Any]:
    candidate = evaluate_candidate(config, candidate_id, level=level)
    return candidate.model_dump(mode="json")


def post_approve(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
) -> dict[str, Any]:
    candidate = approve_candidate(
        config,
        candidate_id,
        force_critical=force_critical,
    )
    return candidate.model_dump(mode="json")


def post_reject(
    config: BridgeConfig,
    candidate_id: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    candidate = reject_candidate(config, candidate_id, reason=reason)
    return candidate.model_dump(mode="json")


def get_diff(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    return diff_candidate(config, candidate_id)


def _candidate_summary(c: CandidateUpdate) -> dict[str, Any]:
    preview = c.content if len(c.content) <= 200 else c.content[:200] + "..."
    return {
        "id": c.id,
        "status": c.status,
        "target_profile_id": c.target_profile_id,
        "source": c.source.type,
        "source_url": c.source.uri,
        "captured_at": c.source.captured_at.isoformat(),
        "rde_class": c.evaluation.rde_class if c.evaluation else None,
        "evaluation_level": c.evaluation.level if c.evaluation else None,
        "content_preview": preview,
    }
