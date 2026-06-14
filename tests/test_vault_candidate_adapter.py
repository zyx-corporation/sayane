"""Tests for Vault-backed CandidateUpdate adapter."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.storage.vault_candidates import VaultCandidateStore
from sayane.vault.contracts import DataClass, VaultStoreError, assert_vault_store_safe_for_production
from sayane.vault.test_crypto import TestOnlyCryptoProvider
from sayane.vault.test_store import CryptoBackedInMemoryTestVaultStore, TestOnlyKeychainProvider


def _vault_and_session(scopes: list[str]):
    keychain = TestOnlyKeychainProvider()
    crypto = TestOnlyCryptoProvider()
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    session = keychain.unlock("candidate-test", scopes)
    return vault, session


def _candidate(candidate_id: str = "c-vault", profile_id: str = "default") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id=profile_id,
        content="candidate content",
        source=CandidateSource(
            type="test",
            uri=None,
            captured_at=datetime.now(UTC),
        ),
        proposal=CandidateProposal(
            section="knowledge.concepts",
            operation="add",
            add=["candidate content"],
            summary="candidate content",
        ),
    )


def test_vault_candidate_save_load_list_delete() -> None:
    vault, session = _vault_and_session(
        [
            "candidate:write",
            "candidate:read",
            "candidate:delete",
            "candidate:key",
        ],
    )
    assert_vault_store_safe_for_production(vault)
    store = VaultCandidateStore(vault, profile_id="default")
    candidate = _candidate()

    record_id = store.save(candidate, session=session)
    loaded = store.load(record_id, session=session)
    listed = store.list(session=session)

    assert loaded is not None
    assert loaded.id == candidate.id
    assert loaded.content == "candidate content"
    assert len(listed) == 1
    assert listed[0].id == candidate.id
    assert vault.records[(DataClass.CANDIDATE, record_id)].ciphertext != b"candidate content"

    store.delete(record_id, session=session)
    assert store.load(record_id, session=session) is None


def test_vault_candidate_list_filters_profile_id() -> None:
    vault, session = _vault_and_session(["candidate:write", "candidate:read", "candidate:key"])
    default_store = VaultCandidateStore(vault, profile_id="default")
    other_store = VaultCandidateStore(vault, profile_id="other")

    default_store.save(_candidate("c-default", "default"), session=session)
    other_store.save(_candidate("c-other", "other"), session=session)

    listed = default_store.list(session=session)
    assert [c.id for c in listed] == ["c-default"]


def test_vault_candidate_requires_write_scope() -> None:
    vault, session = _vault_and_session(["candidate:read", "candidate:key"])
    store = VaultCandidateStore(vault, profile_id="default")

    with pytest.raises(VaultStoreError, match="missing scope"):
        store.save(_candidate(), session=session)


def test_vault_candidate_requires_read_scope() -> None:
    vault, write_session = _vault_and_session(
        ["candidate:write", "candidate:read", "candidate:key"],
    )
    store = VaultCandidateStore(vault, profile_id="default")
    record_id = store.save(_candidate(), session=write_session)

    keychain = TestOnlyKeychainProvider()
    readless = keychain.unlock("candidate-test", ["candidate:key"])
    with pytest.raises(VaultStoreError, match="missing scope"):
        store.load(record_id, session=readless)


def test_vault_candidate_requires_delete_scope() -> None:
    vault, write_session = _vault_and_session(
        ["candidate:write", "candidate:read", "candidate:key"],
    )
    store = VaultCandidateStore(vault, profile_id="default")
    record_id = store.save(_candidate(), session=write_session)

    keychain = TestOnlyKeychainProvider()
    no_delete = keychain.unlock("candidate-test", ["candidate:read", "candidate:key"])
    with pytest.raises(VaultStoreError, match="missing scope"):
        store.delete(record_id, session=no_delete)
