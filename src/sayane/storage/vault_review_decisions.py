"""Vault-backed ReviewDecision repository adapter.

This adapter stores ReviewDecision records through the VaultStore contract. It
is intended as the bridge from Phase 4 FileSystem local working store toward the
Phase 6 Local Vault backend.
"""

from __future__ import annotations

import json
from dataclasses import asdict

from sayane.core.review_decision import ReviewDecision
from sayane.vault.contracts import DataClass, UnlockSession, VaultStore


class VaultReviewDecisionStore:
    """ReviewDecision repository backed by a VaultStore."""

    def __init__(self, vault: VaultStore, *, profile_id: str = "default") -> None:
        self._vault = vault
        self._profile_id = profile_id

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def append(self, decision: ReviewDecision, *, session: UnlockSession) -> str:
        """Append/persist one decision and return its record id."""
        record_id = decision.lineage_event_id
        payload = json.dumps(asdict(decision), ensure_ascii=False).encode("utf-8")
        self._vault.put(
            data_class=DataClass.REVIEW_DECISION,
            record_id=record_id,
            plaintext=payload,
            aad=self._aad(decision),
            session=session,
        )
        return record_id

    def list(self, *, session: UnlockSession) -> list[ReviewDecision]:
        """List persisted ReviewDecision records for this profile."""
        decisions: list[ReviewDecision] = []
        for record_id in self._vault.list_record_ids(DataClass.REVIEW_DECISION, session=session):
            raw = self._vault.get(
                data_class=DataClass.REVIEW_DECISION,
                record_id=record_id,
                session=session,
            )
            if raw is None:
                continue
            data = json.loads(raw.decode("utf-8"))
            if data.get("target_profile_id") not in (None, self._profile_id):
                continue
            # ReviewDecision currently has no target_profile_id field, so bind
            # profile through AAD and store instance profile_id.
            decisions.append(ReviewDecision(**data))
        return decisions

    def get(self, record_id: str, *, session: UnlockSession) -> ReviewDecision | None:
        """Return one persisted ReviewDecision, if present."""
        raw = self._vault.get(
            data_class=DataClass.REVIEW_DECISION,
            record_id=record_id,
            session=session,
        )
        if raw is None:
            return None
        return ReviewDecision(**json.loads(raw.decode("utf-8")))

    def _aad(self, decision: ReviewDecision) -> dict[str, str]:
        return {
            "profile_id": self._profile_id,
            "record_type": "review_decision",
            "candidate_id": decision.candidate_id,
            "decision": decision.decision,
            "schema_version": "review_decision.v1",
        }
