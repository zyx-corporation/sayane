"""ReviewDecision FileSystem local working store.

Phase 4 keeps ReviewDecision records in a local working store and applies the
storage security policy before writes. This is a transitional store until the
Local Vault backend becomes available.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from sayane.bridge.config import BridgeConfig
from sayane.core.review_decision import ReviewDecision
from sayane.storage.security_policy import require_local_working_store


def review_decisions_path(config: BridgeConfig, profile_id: str) -> Path:
    """Return the local working-store path for ReviewDecision records."""
    return config.home / "review_decisions" / f"{profile_id}.jsonl"


def append_review_decision(
    config: BridgeConfig,
    profile_id: str,
    decision: ReviewDecision,
) -> Path:
    """Append one ReviewDecision to the local working store."""
    if config.repositories is not None:
        config.repositories.review_decisions.append(
            decision,
            **config.repository_kwargs(),
        )
        return review_decisions_path(config, profile_id)
    path = review_decisions_path(config, profile_id)
    require_local_working_store(path, record_class="review_decision")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(asdict(decision), ensure_ascii=False) + "\n")
    return path


def list_review_decisions(
    config: BridgeConfig,
    profile_id: str = "default",
    *,
    limit: int | None = None,
) -> list[ReviewDecision]:
    """List persisted ReviewDecision records for a profile."""
    if config.repositories is not None:
        records = config.repositories.review_decisions.list(
            **config.repository_kwargs(),
        )
        if limit is not None:
            return records[-limit:]
        return records
    path = review_decisions_path(config, profile_id)
    if not path.exists():
        return []
    records: list[ReviewDecision] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        data = json.loads(line)
        records.append(ReviewDecision(**data))
    if limit is not None:
        return records[-limit:]
    return records
