"""Tests for Vault-backed lineage adapter."""

from __future__ import annotations

import pytest

from sayane.storage.vault_lineage import VaultLineageStore
from sayane.vault.contracts import DataClass, VaultStoreError, assert_vault_store_safe_for_production
from sayane.vault.test_crypto import TestOnlyCryptoProvider
from sayane.vault.test_store import CryptoBackedInMemoryTestVaultStore, TestOnlyKeychainProvider


def _vault_and_session(scopes: list[str]):
    keychain = TestOnlyKeychainProvider()
    crypto = TestOnlyCryptoProvider()
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    session = keychain.unlock("lineage-test", scopes)
    return vault, session


def test_vault_lineage_append_get_list() -> None:
    vault, session = _vault_and_session(["lineage:write", "lineage:read", "lineage:key"])
    assert_vault_store_safe_for_production(vault)
    store = VaultLineageStore(vault, profile_id="default")

    event_id = store.append(
        "candidate_generated",
        {
            "operation": "candidate_generated",
            "node_kind": "candidate",
            "candidate_id": "c1",
        },
        session=session,
    )

    loaded = store.get(event_id, session=session)
    listed = store.list(session=session)

    assert loaded is not None
    assert loaded["event"] == "candidate_generated"
    assert loaded["candidate_id"] == "c1"
    assert loaded["profile_id"] == "default"
    assert len(listed) == 1
    assert listed[0]["event_id"] == event_id
    assert vault.records[(DataClass.LINEAGE, event_id)].ciphertext != b"candidate_generated"


def test_vault_lineage_list_limit() -> None:
    vault, session = _vault_and_session(["lineage:write", "lineage:read", "lineage:key"])
    store = VaultLineageStore(vault, profile_id="default")

    first = store.append("capture_created", {"candidate_id": "c1"}, session=session)
    second = store.append("candidate_generated", {"candidate_id": "c2"}, session=session)

    listed = store.list(session=session, limit=1)
    assert len(listed) == 1
    assert listed[0]["event_id"] in {first, second}
    assert listed[0]["candidate_id"] == "c2"


def test_vault_lineage_list_filters_profile_id() -> None:
    vault, session = _vault_and_session(["lineage:write", "lineage:read", "lineage:key"])
    default_store = VaultLineageStore(vault, profile_id="default")
    other_store = VaultLineageStore(vault, profile_id="other")

    default_id = default_store.append(
        "capture_created",
        {"candidate_id": "c-default"},
        session=session,
    )
    other_store.append("capture_created", {"candidate_id": "c-other"}, session=session)

    listed = default_store.list(session=session)
    assert [r["event_id"] for r in listed] == [default_id]
    assert [r["candidate_id"] for r in listed] == ["c-default"]


def test_vault_lineage_requires_write_scope() -> None:
    vault, session = _vault_and_session(["lineage:read", "lineage:key"])
    store = VaultLineageStore(vault, profile_id="default")

    with pytest.raises(VaultStoreError, match="missing scope"):
        store.append("candidate_generated", {"candidate_id": "c1"}, session=session)


def test_vault_lineage_requires_read_scope() -> None:
    vault, write_session = _vault_and_session(
        ["lineage:write", "lineage:read", "lineage:key"],
    )
    store = VaultLineageStore(vault, profile_id="default")
    event_id = store.append("candidate_generated", {"candidate_id": "c1"}, session=write_session)

    keychain = TestOnlyKeychainProvider()
    readless = keychain.unlock("lineage-test", ["lineage:key"])
    with pytest.raises(VaultStoreError, match="missing scope"):
        store.get(event_id, session=readless)
