"""Tests for SQLite-backed Local Vault store."""

from __future__ import annotations

import sqlite3

import pytest

from sayane.vault.contracts import DataClass, VaultStoreError, VaultStoreMode
from sayane.vault.sqlite_schema import inspect_sqlite_tables, validate_sqlite_vault_schema
from sayane.vault.sqlite_store import SQLiteVaultStore
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import TestOnlyKeychainProvider


def _store(tmp_path):
    keychain = TestOnlyKeychainProvider()
    key_manager = TestOnlyKeyManager(keychain=keychain)
    crypto = TestOnlyCryptoProvider(key_manager=key_manager)
    store = SQLiteVaultStore(tmp_path / "vault.sqlite", crypto=crypto, store_mode=VaultStoreMode.TEST)
    session = keychain.unlock(
        "sqlite-vault-test",
        [
            "candidate:write",
            "candidate:read",
            "candidate:delete",
            "candidate:key",
        ],
    )
    return store, session


def test_sqlite_vault_store_round_trip_and_schema_contract(tmp_path) -> None:
    store, session = _store(tmp_path)
    aad = {"profile_id": "default", "record_type": "candidate"}

    store.put(DataClass.CANDIDATE, "c1", b"secret candidate", aad, session)
    plaintext = store.get(DataClass.CANDIDATE, "c1", session)

    assert plaintext == b"secret candidate"
    assert store.mode() == VaultStoreMode.TEST
    assert store.is_plaintext_default() is False
    assert validate_sqlite_vault_schema(inspect_sqlite_tables(store.path)) == []


def test_sqlite_vault_store_persists_ciphertext_not_plaintext(tmp_path) -> None:
    store, session = _store(tmp_path)
    store.put(
        DataClass.CANDIDATE,
        "c1",
        b"secret candidate",
        {"profile_id": "default", "record_type": "candidate"},
        session,
    )

    connection = sqlite3.connect(store.path)
    try:
        row = connection.execute(
            "SELECT ciphertext, aad_json FROM encrypted_records WHERE data_class = ? AND record_id = ?",
            (DataClass.CANDIDATE.value, "c1"),
        ).fetchone()
    finally:
        connection.close()

    assert row is not None
    assert b"secret candidate" not in row[0]
    assert "profile_id" in row[1]


def test_sqlite_vault_store_lists_and_deletes_records(tmp_path) -> None:
    store, session = _store(tmp_path)
    aad = {"profile_id": "default", "record_type": "candidate"}
    store.put(DataClass.CANDIDATE, "c1", b"one", aad, session)
    store.put(DataClass.CANDIDATE, "c2", b"two", aad, session)

    assert store.list_record_ids(DataClass.CANDIDATE, session) == ["c1", "c2"]

    store.delete(DataClass.CANDIDATE, "c1", session)

    assert store.list_record_ids(DataClass.CANDIDATE, session) == ["c2"]
    with pytest.raises(VaultStoreError, match="record not found"):
        store.get(DataClass.CANDIDATE, "c1", session)


def test_sqlite_vault_store_requires_scope(tmp_path) -> None:
    store, session = _store(tmp_path)
    narrow = type(session)(
        session_id="narrow",
        purpose="narrow",
        scopes=("candidate:read", "candidate:key"),
        assurance=session.assurance,
        unlocked_at=session.unlocked_at,
        expires_at=session.expires_at,
        idle_expires_at=session.idle_expires_at,
    )

    with pytest.raises(VaultStoreError, match="missing scope"):
        store.put(
            DataClass.CANDIDATE,
            "c1",
            b"secret",
            {"profile_id": "default"},
            narrow,
        )
