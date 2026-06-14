"""Tests for SQLite-backed Local Vault store."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

import pytest

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.review_decision import ReviewDecision
from sayane.vault.contracts import DataClass, VaultStoreError, VaultStoreMode
from sayane.vault.sqlite_runtime import build_sqlite_test_vault_runtime
from sayane.vault.sqlite_schema import inspect_sqlite_tables, validate_sqlite_vault_schema
from sayane.vault.sqlite_store import SQLiteVaultStore
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import TestOnlyKeychainProvider


def _store(tmp_path):
    keychain = TestOnlyKeychainProvider()
    key_manager = TestOnlyKeyManager(keychain=keychain)
    crypto = TestOnlyCryptoProvider(key_manager=key_manager)
    store = SQLiteVaultStore(
        tmp_path / "vault.sqlite",
        crypto=crypto,
        store_mode=VaultStoreMode.TEST,
    )
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


def _candidate(candidate_id: str = "c-sqlite") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="sqlite candidate content",
        source=CandidateSource(
            type="test",
            uri=None,
            captured_at=datetime.now(UTC),
        ),
        proposal=CandidateProposal(
            section="knowledge.concepts",
            add=["sqlite candidate content"],
        ),
    )


def test_sqlite_vault_store_round_trip_and_schema_contract(tmp_path) -> None:
    store, session = _store(tmp_path)
    aad = {"profile_id": "default", "record_type": "candidate"}

    store.put(
        data_class=DataClass.CANDIDATE,
        record_id="c1",
        plaintext=b"secret candidate",
        aad=aad,
        session=session,
    )
    plaintext = store.get(
        data_class=DataClass.CANDIDATE,
        record_id="c1",
        session=session,
    )

    assert plaintext == b"secret candidate"
    assert store.mode() == VaultStoreMode.TEST
    assert store.is_plaintext_default() is False
    assert validate_sqlite_vault_schema(inspect_sqlite_tables(store.path)) == []


def test_sqlite_vault_store_persists_ciphertext_not_plaintext(tmp_path) -> None:
    store, session = _store(tmp_path)
    store.put(
        data_class=DataClass.CANDIDATE,
        record_id="c1",
        plaintext=b"secret candidate",
        aad={"profile_id": "default", "record_type": "candidate"},
        session=session,
    )

    connection = sqlite3.connect(store.path)
    try:
        row = connection.execute(
            """
            SELECT ciphertext, aad_json
            FROM encrypted_records
            WHERE data_class = ? AND record_id = ?
            """,
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
    store.put(
        data_class=DataClass.CANDIDATE,
        record_id="c1",
        plaintext=b"one",
        aad=aad,
        session=session,
    )
    store.put(
        data_class=DataClass.CANDIDATE,
        record_id="c2",
        plaintext=b"two",
        aad=aad,
        session=session,
    )

    assert store.list_record_ids(DataClass.CANDIDATE, session=session) == ["c1", "c2"]

    store.delete(data_class=DataClass.CANDIDATE, record_id="c1", session=session)

    assert store.list_record_ids(DataClass.CANDIDATE, session=session) == ["c2"]
    with pytest.raises(VaultStoreError, match="record not found"):
        store.get(data_class=DataClass.CANDIDATE, record_id="c1", session=session)


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
            data_class=DataClass.CANDIDATE,
            record_id="c1",
            plaintext=b"secret",
            aad={"profile_id": "default"},
            session=narrow,
        )


def test_sqlite_test_runtime_builder_is_explicit_and_not_plaintext(tmp_path) -> None:
    runtime = build_sqlite_test_vault_runtime(
        path=tmp_path / "vault.sqlite",
        profile_id="default",
    )

    assert runtime.mode == VaultStoreMode.TEST
    assert runtime.vault.mode() == VaultStoreMode.TEST
    assert runtime.vault.is_plaintext_default() is False
    assert validate_sqlite_vault_schema(inspect_sqlite_tables(runtime.vault.path)) == []


def test_sqlite_test_runtime_repository_bundle_round_trip(tmp_path) -> None:
    runtime = build_sqlite_test_vault_runtime(
        path=tmp_path / "vault.sqlite",
        profile_id="default",
    )
    session = runtime.keychain.unlock(
        "sqlite-runtime-bundle-test",
        [
            "candidate:write",
            "candidate:read",
            "candidate:key",
            "review_decision:write",
            "review_decision:read",
            "review_decision:key",
            "lineage:write",
            "lineage:read",
            "lineage:key",
        ],
    )

    candidate_id = runtime.repositories.candidates.save(_candidate(), session=session)
    decision_id = runtime.repositories.review_decisions.append(
        ReviewDecision(candidate_id=candidate_id, decision="approve", reason="ok"),
        session=session,
    )
    lineage_id = runtime.repositories.lineage.append(
        "candidate_approved",
        {"candidate_id": candidate_id, "operation": "candidate_approved"},
        session=session,
    )

    candidate = runtime.repositories.candidates.load(candidate_id, session=session)
    decision = runtime.repositories.review_decisions.get(decision_id, session=session)
    lineage = runtime.repositories.lineage.get(lineage_id, session=session)

    assert candidate is not None
    assert candidate.content == "sqlite candidate content"
    assert decision is not None
    assert decision.decision == "approve"
    assert lineage is not None
    assert lineage["candidate_id"] == candidate_id
    assert runtime.repositories.smoke_check(session=session) == {
        "profile_id": "default",
        "candidate_count": 1,
        "review_decision_count": 1,
        "lineage_count": 1,
    }
