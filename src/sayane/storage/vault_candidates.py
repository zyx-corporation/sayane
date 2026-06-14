"""Vault-backed CandidateUpdate repository adapter.

This adapter stores CandidateUpdate records through the VaultStore contract. It
is intended as the bridge from Phase 4 FileSystem local working store toward the
Phase 6 Local Vault backend.
"""

from __future__ import annotations

import json

from sayane.core.candidate import CandidateUpdate
from sayane.vault.contracts import DataClass, UnlockSession, VaultStore


class VaultCandidateStore:
    """CandidateUpdate repository backed by a VaultStore."""

    def __init__(self, vault: VaultStore, *, profile_id: str = "default") -> None:
        self._vault = vault
        self._profile_id = profile_id

    @property
    def profile_id(self) -> str:
        return self._profile_id

    def save(self, candidate: CandidateUpdate, *, session: UnlockSession) -> str:
        """Persist one CandidateUpdate and return its record id."""
        record_id = candidate.id
        payload = json.dumps(
            candidate.model_dump(mode="json"),
            ensure_ascii=False,
        ).encode("utf-8")
        self._vault.put(
            data_class=DataClass.CANDIDATE,
            record_id=record_id,
            plaintext=payload,
            aad=self._aad(candidate),
            session=session,
        )
        return record_id

    def load(self, candidate_id: str, *, session: UnlockSession) -> CandidateUpdate | None:
        """Load one CandidateUpdate, if present."""
        raw = self._vault.get(
            data_class=DataClass.CANDIDATE,
            record_id=candidate_id,
            session=session,
        )
        if raw is None:
            return None
        return CandidateUpdate.model_validate(json.loads(raw.decode("utf-8")))

    def list(self, *, session: UnlockSession) -> list[CandidateUpdate]:
        """List CandidateUpdate records for this profile."""
        candidates: list[CandidateUpdate] = []
        for candidate_id in self._vault.list_record_ids(DataClass.CANDIDATE, session=session):
            candidate = self.load(candidate_id, session=session)
            if candidate is None:
                continue
            if candidate.target_profile_id != self._profile_id:
                continue
            candidates.append(candidate)
        return candidates

    def delete(self, candidate_id: str, *, session: UnlockSession) -> None:
        """Delete one CandidateUpdate record."""
        self._vault.delete(
            data_class=DataClass.CANDIDATE,
            record_id=candidate_id,
            session=session,
        )

    def _aad(self, candidate: CandidateUpdate) -> dict[str, str]:
        aad = {
            "profile_id": self._profile_id,
            "record_type": "candidate",
            "candidate_id": candidate.id,
            "status": candidate.status,
            "schema_version": "candidate_update.v1",
        }
        if candidate.proposal.section:
            aad["section"] = candidate.proposal.section
        if candidate.source.type:
            aad["source_type"] = candidate.source.type
        return aad
