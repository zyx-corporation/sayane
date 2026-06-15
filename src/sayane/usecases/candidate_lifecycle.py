"""Candidate lifecycle usecases for evaluate / approve / reject."""

from __future__ import annotations

from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.domain.candidate_policy import (
    ensure_can_approve,
    ensure_can_evaluate,
    ensure_can_reject,
)
from sayane.evaluators.service import approve_candidate, evaluate_candidate, reject_candidate
from sayane.storage.candidates import load_candidate


def evaluate_candidate_for_api(
    config: BridgeConfig,
    candidate_id: str,
    *,
    level: int = 1,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    ensure_can_evaluate(existing, candidate_id)
    candidate = evaluate_candidate(config, candidate_id, level=level)
    return candidate.model_dump(mode="json")


def approve_candidate_for_api(
    config: BridgeConfig,
    candidate_id: str,
    *,
    force_critical: bool = False,
    override_reason: str | None = None,
    explicit_confirmation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    ensure_can_approve(
        existing,
        candidate_id,
        force_critical=force_critical,
        explicit_confirmation=explicit_confirmation,
    )
    candidate = approve_candidate(
        config,
        candidate_id,
        force_critical=force_critical,
        override_reason=override_reason,
    )
    return candidate.model_dump(mode="json")


def reject_candidate_for_api(
    config: BridgeConfig,
    candidate_id: str,
    *,
    reason: str | None = None,
) -> dict[str, Any]:
    existing = load_candidate(config, candidate_id)
    ensure_can_reject(existing, candidate_id)
    candidate = reject_candidate(config, candidate_id, reason=reason)
    return candidate.model_dump(mode="json")
