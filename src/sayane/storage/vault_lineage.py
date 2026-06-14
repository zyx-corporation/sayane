"""Vault-backed lineage repository adapter.

This adapter stores lineage events through the VaultStore contract. It bridges
Phase 4 append-only JSONL lineage toward the Phase 6 Local Vault backend.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from sayane.vault.contracts import DataClass, UnlockSession, VaultStore


class VaultLineageStore:
    """Append-only lineage repository backed by a VaultStore."""

    def __init__(self, vault: VaultStore, *, profile_id: str = "default") -> None:
        self._vault = vault
        self._profile_id = profile_id

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def append(
        self,
        event: str,
        payload: dict[str, Any],
        *,
        session: UnlockSession,
    ) -> str:
        """Append one lineage event and return its record id."""
        record_id = str(payload.get("event_id") or uuid4().hex)
        record = {
            "event": event,
            "at": datetime.now(UTC).isoformat(),
            "profile_id": self._profile_id,
            **payload,
            "event_id": record_id,
        }
        plaintext = json.dumps(record, ensure_ascii=False).encode("utf-8")
        self._vault.put(
            data_class=DataClass.LINEAGE,
            record_id=record_id,
            plaintext=plaintext,
            aad=self._aad(record),
            session=session,
        )
        return record_id

    def list(self, *, session: UnlockSession, limit: int | None = None) -> list[dict[str, Any]]:
        """List persisted lineage events for this profile."""
        records: list[dict[str, Any]] = []
        for record_id in self._vault.list_record_ids(DataClass.LINEAGE, session=session):
            raw = self._vault.get(
                data_class=DataClass.LINEAGE,
                record_id=record_id,
                session=session,
            )
            if raw is None:
                continue
            data = json.loads(raw.decode("utf-8"))
            if data.get("profile_id") != self._profile_id:
                continue
            records.append(data)
        records.sort(key=lambda item: item.get("at", ""))
        if limit is not None:
            return records[-limit:]
        return records

    def get(self, record_id: str, *, session: UnlockSession) -> dict[str, Any] | None:
        """Return one lineage event, if present."""
        raw = self._vault.get(
            data_class=DataClass.LINEAGE,
            record_id=record_id,
            session=session,
        )
        if raw is None:
            return None
        data = json.loads(raw.decode("utf-8"))
        if data.get("profile_id") != self._profile_id:
            return None
        return data

    def _aad(self, record: dict[str, Any]) -> dict[str, str]:
        aad = {
            "profile_id": self._profile_id,
            "record_type": "lineage",
            "event_id": str(record.get("event_id") or ""),
            "event": str(record.get("event") or ""),
            "schema_version": "lineage.v1",
        }
        operation = record.get("operation")
        if operation:
            aad["operation"] = str(operation)
        node_kind = record.get("node_kind")
        if node_kind:
            aad["node_kind"] = str(node_kind)
        return aad
