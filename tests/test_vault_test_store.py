"""Tests for test-only in-memory vault implementation."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sayane.vault.contracts import (
    DataClass,
    SecretStoreAssurance,
    UnlockSession,
    VaultStoreError,
    assert_vault_store_safe_for_production,
)
from sayane.vault.test_store import InMemoryTestVaultStore, TestOnlyKeychainProvider


def test_test_only_keychain_provider_reports_test_assurance() -> None:
    provider = TestOnlyKeychainProvider()
    caps = provider.capabilities()
    assert caps.platform_name == "test-only"
    assert caps.assurance == SecretStoreAssurance.TEST_ONLY
    assert caps.supports_biometric_unlock is False


def test_test_only_keychain_unlock_and_lock() -> None:
    provider = TestOnlyKeychainProvider()
    session = provider.unlock("unit-test", ["candidate:read"])
    assert session.allows("candidate:read") is True
    assert session.session_id in provider.active_sessions
    provider.lock(session.session_id)
    assert session.session_id not in provider.active_sessions


def test_in_memory_test_vault_put_get_delete() -> None:
    provider = TestOnlyKeychainProvider()
    session = provider.unlock(
        "unit-test",
        ["candidate:write", "candidate:read", "candidate:delete"],
    )
    store = InMemoryTestVaultStore()

    record = store.put(
        data_class=DataClass.CANDIDATE,
        record_id="c1",
        plaintext=b"candidate content",
        aad={"profile_id": "default"},
        session=session,
    )
    assert record.ciphertext != b"candidate content"
    assert store.list_record_ids(DataClass.CANDIDATE) == ["c1"]
    assert store.get(data_class=DataClass.CANDIDATE, record_id="c1", session=session) == b"candidate content"

    store.delete(data_class=DataClass.CANDIDATE, record_id="c1", session=session)
    assert store.get(data_class=DataClass.CANDIDATE, record_id="c1", session=session) is None


def test_in_memory_test_vault_enforces_scope() -> None:
    provider = TestOnlyKeychainProvider()
    session = provider.unlock("unit-test", ["candidate:read"])
    store = InMemoryTestVaultStore()

    with pytest.raises(VaultStoreError, match="missing scope"):
        store.put(
            data_class=DataClass.CANDIDATE,
            record_id="c1",
            plaintext=b"candidate content",
            aad={},
            session=session,
        )


def test_in_memory_test_vault_rejects_expired_session() -> None:
    now = datetime.now(UTC)
    session = UnlockSession(
        session_id="expired",
        purpose="unit-test",
        scopes=("candidate:write",),
        assurance=SecretStoreAssurance.TEST_ONLY,
        unlocked_at=now - timedelta(minutes=10),
        expires_at=now - timedelta(seconds=1),
    )
    store = InMemoryTestVaultStore()

    with pytest.raises(VaultStoreError, match="expired"):
        store.put(
            data_class=DataClass.CANDIDATE,
            record_id="c1",
            plaintext=b"candidate content",
            aad={},
            session=session,
        )


def test_in_memory_test_vault_is_safe_only_because_mode_is_test() -> None:
    store = InMemoryTestVaultStore()
    assert store.is_plaintext_default() is True
    assert_vault_store_safe_for_production(store)
