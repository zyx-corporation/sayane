"""Tests for VaultRepositoryBundle."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.review_decision import ReviewDecision
from sayane.storage.vault_bundle import build_vault_repository_bundle
from sayane.vault.contracts import VaultStoreError
from sayane.vault.test_crypto import TestOnlyCryptoProvider
from sayane.vault.test_store import CryptoBackedInMemoryTestVaultStore, TestOnlyKeychainProvider


def _candidate(candidate_id: str = "c-bundle") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="candidate content",
        source=CandidateSource(type="test", uri=None, captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=["candidate content"]),
    )


def _bundle_and_session(scopes: list[str]):
    keychain = TestOnlyKeychainProvider()
    crypto = TestOnlyCryptoProvider()
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    bundle = build_vault_repository_bundle(vault, profile_id="default")
    session = keychain.unlock("bundle-test", scopes)
    return bundle, session


def test_vault_repository_bundle_groups_repositories() -> None:
    bundle, session = _bundle_and_session(
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

    bundle.candidates.save(_candidate(), session=session)
    bundle.review_decisions.append(
        ReviewDecision(candidate_id="c-bundle", decision="approve", reason="ok"),
        session=session,
    )
    bundle.lineage.append(
        "candidate_approved",
        {"candidate_id": "c-bundle", "operation": "candidate_approved"},
        session=session,
    )

    assert bundle.smoke_check(session=session) == {
        "profile_id": "default",
        "candidate_count": 1,
        "review_decision_count": 1,
        "lineage_count": 1,
    }


def test_vault_repository_bundle_smoke_check_requires_read_scopes() -> None:
    bundle, session = _bundle_and_session(["candidate:read", "candidate:key"])

    with pytest.raises(VaultStoreError, match="missing scope"):
        bundle.smoke_check(session=session)
