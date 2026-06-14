"""Tests for test-only vault KeyManager and CryptoProvider."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sayane.vault.contracts import DataClass, SecretStoreAssurance, UnlockSession, VaultStoreError
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import TestOnlyKeychainProvider


def _session(scopes: tuple[str, ...] = ("*",), seconds: int = 60) -> UnlockSession:
    now = datetime.now(UTC)
    return UnlockSession(
        session_id="s-test",
        purpose="unit-test",
        scopes=scopes,
        assurance=SecretStoreAssurance.TEST_ONLY,
        unlocked_at=now,
        expires_at=now + timedelta(seconds=seconds),
    )


def test_key_manager_creates_separate_deks_per_data_class() -> None:
    km = TestOnlyKeyManager(TestOnlyKeychainProvider())
    session = _session(scopes=("candidate:key", "review_decision:key"))

    candidate_key = km.get_or_create_dek(DataClass.CANDIDATE, session=session)
    review_key = km.get_or_create_dek(DataClass.REVIEW_DECISION, session=session)

    assert candidate_key.data_class == DataClass.CANDIDATE
    assert review_key.data_class == DataClass.REVIEW_DECISION
    assert candidate_key.material != review_key.material
    assert DataClass.CANDIDATE in km.keyring
    assert DataClass.REVIEW_DECISION in km.keyring


def test_key_manager_requires_scope() -> None:
    km = TestOnlyKeyManager(TestOnlyKeychainProvider())
    session = _session(scopes=("profile:key",))

    with pytest.raises(VaultStoreError, match="missing scope"):
        km.get_or_create_dek(DataClass.CANDIDATE, session=session)


def test_key_manager_rotates_and_destroys_dek() -> None:
    km = TestOnlyKeyManager(TestOnlyKeychainProvider())
    session = _session(scopes=("candidate:key",))

    first = km.get_or_create_dek(DataClass.CANDIDATE, session=session)
    rotated_entry = km.rotate_dek(DataClass.CANDIDATE)
    second = km.get_or_create_dek(DataClass.CANDIDATE, session=session)

    assert rotated_entry.rotated_at is not None
    assert first.key_id != second.key_id
    assert first.material != second.material

    km.destroy_dek(DataClass.CANDIDATE)
    assert DataClass.CANDIDATE not in km.keyring


def test_crypto_provider_round_trips_with_aad() -> None:
    crypto = TestOnlyCryptoProvider()
    session = _session(scopes=("candidate:key",))
    aad = {"profile_id": "default", "record_type": "candidate"}

    record = crypto.encrypt_record(
        record_id="c1",
        data_class=DataClass.CANDIDATE,
        plaintext=b"candidate content",
        aad=aad,
        session=session,
    )

    assert record.ciphertext != b"candidate content"
    decrypted = crypto.decrypt_record(record, session=session)
    assert decrypted == b"candidate content"


def test_crypto_provider_detects_aad_mismatch() -> None:
    crypto = TestOnlyCryptoProvider()
    session = _session(scopes=("candidate:key",))

    record = crypto.encrypt_record(
        record_id="c1",
        data_class=DataClass.CANDIDATE,
        plaintext=b"candidate content",
        aad={"profile_id": "default"},
        session=session,
    )
    tampered = type(record)(
        record_id=record.record_id,
        data_class=record.data_class,
        key_id=record.key_id,
        nonce=record.nonce,
        ciphertext=record.ciphertext,
        aad={"profile_id": "other"},
        created_at=record.created_at,
        algorithm=record.algorithm,
    )

    with pytest.raises(VaultStoreError, match="AAD integrity"):
        crypto.decrypt_record(tampered, session=session)


def test_crypto_provider_fails_after_dek_destroyed() -> None:
    crypto = TestOnlyCryptoProvider()
    session = _session(scopes=("candidate:key",))

    record = crypto.encrypt_record(
        record_id="c1",
        data_class=DataClass.CANDIDATE,
        plaintext=b"candidate content",
        aad={},
        session=session,
    )
    crypto.key_manager.destroy_dek(DataClass.CANDIDATE)

    with pytest.raises(VaultStoreError, match="missing keyring"):
        crypto.decrypt_record(record, session=session)
