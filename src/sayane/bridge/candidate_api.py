"""Bridge-facing facade for Candidate evaluate / approve flow."""

from __future__ import annotations

from typing import Any

from sayane.bridge.candidate_presenter import candidate_summary, source_excerpt
from sayane.bridge.config import BridgeConfig
from sayane.domain.candidate_policy import CandidateOperationError, UNSAFE_APPROVE_CATEGORIES
from sayane.evaluators.service import diff_candidate
from sayane.storage.candidates import list_candidate_ids, load_candidate
from sayane.usecases.candidate_lifecycle import (
    approve_candidate_for_api,
    evaluate_candidate_for_api,
    reject_candidate_for_api,
)
from sayane.usecases.candidate_lineage import (
    get_candidate_lineage_for_api,
    get_capture_lineage_for_api,
)
from sayane.usecases.candidate_revision import revise_candidate_for_api

# Backward-compatible aliases for older internal/private imports.
_source_excerpt = source_excerpt
_candidate_summary = candidate_summary


def list_candidates(config: BridgeConfig) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for cid in list_candidate_ids(config):
        try:
            candidate = load_candidate(config, cid)
            items.append(candidate_summary(candidate))
        except Exception:
            continue
    return items


def get_candidate(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    candidate = load_candidate(config, candidate_id)
    data = candidate.model_dump(mode="json")
    data["source_excerpt"] = source_excerpt(candidate)
    return data


def post_evaluate(
    config: BridgeConfig,
    candidate_id: str,
    *,
    level: int = 1,
) -> dict[str, Any]:
    return evaluate_candidate_for_api(config, candidate_id, level=level)


def post_approve(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
    override_reason: str | None = None,
    explicit_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return approve_candidate_for_api(
        config,
        candidate_id,
        force_critical=force_critical,
        override_reason=override_reason,
        explicit_confirmation=explicit_confirmation,
    )


def post_reject(
    config: BridgeConfig,
    candidate_id: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    return reject_candidate_for_api(config, candidate_id, reason=reason)


def get_diff(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    return diff_candidate(config, candidate_id)


def get_candidate_lineage(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    return get_candidate_lineage_for_api(config, candidate_id)


def get_capture_lineage(config: BridgeConfig, capture_id: str) -> dict[str, Any]:
    return get_capture_lineage_for_api(config, capture_id)


def post_revise(
    config: BridgeConfig,
    candidate_id: str,
    *,
    edited_text: str,
    target_section: str | None = None,
    change_reason: str | None = None,
) -> dict[str, Any]:
    return revise_candidate_for_api(
        config,
        candidate_id,
        edited_text=edited_text,
        target_section=target_section,
        change_reason=change_reason,
    )


__all__ = [
    "CandidateOperationError",
    "UNSAFE_APPROVE_CATEGORIES",
    "list_candidates",
    "get_candidate",
    "post_evaluate",
    "post_approve",
    "post_reject",
    "get_diff",
    "get_candidate_lineage",
    "get_capture_lineage",
    "post_revise",
]
