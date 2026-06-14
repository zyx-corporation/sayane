"""Append-only lineage records per profile."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.storage.security_policy import require_local_working_store


def lineage_path(config: BridgeConfig, profile_id: str) -> Path:
    return config.home / "lineage" / f"{profile_id}.jsonl"


def append_record(
    config: BridgeConfig,
    profile_id: str,
    event: str,
    payload: dict[str, Any],
) -> Path:
    path = lineage_path(config, profile_id)
    require_local_working_store(path, record_class="lineage")
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "event": event,
        "at": datetime.now(UTC).isoformat(),
        **payload,
    }
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def list_records(config: BridgeConfig, profile_id: str, limit: int = 50) -> list[dict[str, Any]]:
    path = lineage_path(config, profile_id)
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    records = [json.loads(line) for line in lines if line.strip()]
    return records[-limit:]
