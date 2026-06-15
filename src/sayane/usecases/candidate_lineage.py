"""Candidate and capture lineage API usecases."""

from __future__ import annotations

from typing import Any

from sayane.bridge.config import BridgeConfig


def get_candidate_lineage_for_api(config: BridgeConfig, candidate_id: str) -> dict[str, Any]:
    from sayane.lineage.query import build_candidate_lineage

    lineage = build_candidate_lineage(config, candidate_id)
    return lineage.model_dump(mode="json")


def get_capture_lineage_for_api(config: BridgeConfig, capture_id: str) -> dict[str, Any]:
    from sayane.lineage.query import build_capture_lineage

    lineage = build_capture_lineage(config, capture_id)
    return lineage.model_dump(mode="json")
