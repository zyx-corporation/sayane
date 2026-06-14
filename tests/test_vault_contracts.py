"""Tests for Local Vault interface contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest

from sayane.vault.contracts import (
    DataClass,
    EncryptedRecord,
    SecretStoreAssurance,
    UnlockSession,
    VaultStoreError,
    VaultStoreMode,
    assert_vault_store_safe_for_production,
)


def _session(scopes: tuple[str, ...] = ("*",), seconds: int = 60) -> UnlockSession:
    now = datetime.now(UTC)
    return UnlockSession(
        session_id="s-test",
        purpose="test",
        scopes=scopes,
        assurance=SecretStoreAssurance.TEST_ONLY,
        unlocked_at=now,
        expires_at=now + timedelta(seconds=seconds),
    )


def test_unlock_session_checks_scope() -> None:
    session = _session(scopes=("profile:read", "candidate:review"))
    assert session.allows("profile:read") is True
    assert session.allows("candidate:review") is True
    assert session.allows("mcp:compiled_context") is False


def test_unlock_session_wildcard_scope() -> None:
    session = _session(scopes=("*",))
    assert session.allows("deep_private:read") is True


def test_unlock_session_expires() -> None:
    now = datetime.now(UTC)
    session = UnlockSession(
        session_id="s-expired",
        purpose="test",
        scopes=("profile:read",),
        assurance=SecretStoreAssurance.TEST_ONLY,
        unlocked_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(seconds=1),
    )
    assert session.is_expired(now=now) is True


def test_unlock_session_idle_expiry() -> None:
    now = datetime.now(UTC)
    session = UnlockSession(
        session_id="s-idle",
        purpose="test",
        scopes=("profile:read",),
        assurance=SecretStoreAssurance.TEST_ONLY,
        unlocked_at=now - timedelta(minutes=10),
        expires_at=now + timedelta(minutes=10),
        idle_expires_at=now - timedelta(seconds=1),
    )
    assert session.is_expired(now=now) is True


@dataclass
class _PlaintextProductionStore:
    def mode(self) -> VaultStoreMode:
        return VaultStoreMode.PRODUCTION

    def is_plaintext_default(self) -> bool:
        return True

    def put(self, *, data_class, record_id, plaintext, aad, session):
        return EncryptedRecord(
            record_id=record_id,
            data_class=data_class,
            key_id="plain-test",
            nonce=b"",
            ciphertext=plaintext,
            aad=aad,
            created_at=datetime.now(UTC),
            algorithm="plaintext-test",
        )

    def get(self, *, data_class, record_id, session):
        return None

    def delete(self, *, data_class, record_id, session) -> None:
        return None

    def list_record_ids(self, data_class) -> list[str]:
        return []


@dataclass
class _TestPlaintextStore(_PlaintextProductionStore):
    def mode(self) -> VaultStoreMode:
        return VaultStoreMode.TEST


def test_plaintext_store_cannot_be_production_default() -> None:
    with pytest.raises(VaultStoreError, match="plaintext vault store"):
        assert_vault_store_safe_for_production(_PlaintextProductionStore())


def test_plaintext_store_allowed_only_as_explicit_test_store() -> None:
    assert_vault_store_safe_for_production(_TestPlaintextStore())


def test_data_class_has_high_sensitivity_boundaries() -> None:
    assert DataClass.CANDIDATE.value == "candidate"
    assert DataClass.REVIEW_DECISION.value == "review_decision"
    assert DataClass.LINEAGE.value == "lineage"
    assert DataClass.RAW_CAPTURE.value == "raw_capture"
    assert DataClass.DEEP_PRIVATE.value == "deep_private"
