"""Lineage repository backed by ~/.sayane/lineage/*.jsonl."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.storage import lineage_store


class FileSystemLineageStore:
    """File-based lineage store (Community Edition default)."""

    def __init__(self, config: BridgeConfig, profile_id: str) -> None:
        self._config = config
        self._profile_id = profile_id

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def append(self, event: str, payload: dict[str, Any]) -> Path:
        return lineage_store.append_record(self._config, self._profile_id, event, payload)

    def list(self, limit: int = 50) -> list[dict[str, Any]]:
        return lineage_store.list_records(self._config, self._profile_id, limit=limit)
