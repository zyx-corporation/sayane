"""Tests for Vault-backed ReviewDecision adapter."""

from __future__ import annotations

import pytest

from sayane.core.review_decision import ReviewDecision
from sayane.storage.vault_review_decisions import VaultReviewDecisionStore
from sayane.vault.contracts import DataClass, VaultStoreError, assert_vault_store_safe_for_production
from sayane.vault.test_crypto import TestOnlyCryptoProvider
from sayane.vault.test_store import CryptoBackedInMemoryTestVaultStore, TestOnlyKeychainProvider


def _vault_and_session(scopes: list[str]):
    keychain = TestOnlyKeychainProvider()
    crypto = TestOnlyCryptoProvider()
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    session = keychain.unlock("review-decision-test", scopes)
    return vault, session


def test_vault_review_decision_append_get_list() -> None:
    vault, session = _vault_and_session(
        [
            "review_decision:write",
            "review_decision:read",
            "review_decision:key",
        ],
    )
    assert_vault_store_safe_for_production(vault)
    store = VaultReviewDecisionStore(vault, profile_id="default")
    decision = ReviewDecision(
        candidate_id="c-approved",
        decision="approve",
        reason="Approved after review.",
        applied_value="approved content",
        original_section="knowledge.concepts",
        original_action="add",
        original_proposed="approved content",
    )

    record_id = store.append(decision, session=session)
    loaded = store.get(record_id, session=session)
    listed = store.list(session=session)

    assert loaded is not None
    assert loaded.candidate_id == "c-approved"
    assert loaded.applied_value == "approved content"
    assert len(listed) == 1
    assert listed[0].lineage_event_id == decision.lineage_event_id
    assert (
        vault.records[(DataClass.REVIEW_DECISION, record_id)].ciphertext
        != b"approved content"
    )


def test_vault_review_decision_requires_write_scope() -> None:
    vault, session = _vault_and_session(["review_decision:read", "review_decision:key"])
    store = VaultReviewDecisionStore(vault, profile_id="default")

    with pytest.raises(VaultStoreError, match="missing scope"):
        store.append(
            ReviewDecision(candidate_id="c1", decision="approve", reason="ok"),
            session=session,
        )


def test_vault_review_decision_requires_read_scope() -> None:
    vault, write_session = _vault_and_session(
        ["review_decision:write", "review_decision:read", "review_decision:key"],
    )
    store = VaultReviewDecisionStore(vault, profile_id="default")
    record_id = store.append(
        ReviewDecision(candidate_id="c1", decision="approve", reason="ok"),
        session=write_session,
    )

    keychain = TestOnlyKeychainProvider()
    readless = keychain.unlock("review-decision-test", ["review_decision:key"])
    with pytest.raises(VaultStoreError, match="missing scope"):
        store.get(record_id, session=readless)
