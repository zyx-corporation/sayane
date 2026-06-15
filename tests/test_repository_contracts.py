"""Tests for ADR 0007 repository contracts and test providers."""

from __future__ import annotations

from datetime import UTC, datetime

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.review_decision import ReviewDecision
from sayane.storage.repositories import (
    CandidateRepository,
    LineageRepository,
    ProfileContextRepository,
    ProjectContextRepository,
    RepositoryBundle,
    ReviewDecisionRepository,
    TestOnlyInMemoryCandidateRepository,
    TestOnlyInMemoryLineageRepository,
    TestOnlyInMemoryProfileContextRepository,
    TestOnlyInMemoryProjectContextRepository,
    TestOnlyInMemoryReviewDecisionRepository,
    build_test_repository_bundle,
    review_decision_to_payload,
)
from sayane.storage.vault_bundle import build_vault_repository_bundle
from sayane.vault.test_crypto import TestOnlyCryptoProvider
from sayane.vault.test_store import CryptoBackedInMemoryTestVaultStore, TestOnlyKeychainProvider


def _candidate(candidate_id: str = "candidate-1") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="candidate content",
        source=CandidateSource(type="test", uri=None, captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=["candidate content"]),
    )


def _decision(candidate_id: str = "candidate-1") -> ReviewDecision:
    return ReviewDecision(candidate_id=candidate_id, decision="approve", reason="ok")


def test_in_memory_candidate_repository_contract() -> None:
    repo = TestOnlyInMemoryCandidateRepository()
    candidate = _candidate()

    assert isinstance(repo, CandidateRepository)
    assert repo.save(candidate) == candidate.id
    assert repo.load(candidate.id) == candidate
    assert repo.list() == [candidate]

    repo.delete(candidate.id)
    assert repo.load(candidate.id) is None


def test_in_memory_review_decision_repository_contract() -> None:
    repo = TestOnlyInMemoryReviewDecisionRepository()
    decision = _decision()

    assert isinstance(repo, ReviewDecisionRepository)
    record_id = repo.append(decision)
    assert record_id == decision.lineage_event_id
    assert repo.get(record_id) == decision
    assert repo.list() == [decision]


def test_in_memory_lineage_repository_contract() -> None:
    repo = TestOnlyInMemoryLineageRepository()

    assert isinstance(repo, LineageRepository)
    record_id = repo.append("candidate_created", {"candidate_id": "candidate-1"})
    assert repo.get(record_id) == {
        "event": "candidate_created",
        "candidate_id": "candidate-1",
        "event_id": record_id,
    }
    assert repo.list() == [repo.get(record_id)]


def test_in_memory_profile_context_repository_contract() -> None:
    repo = TestOnlyInMemoryProfileContextRepository()

    assert isinstance(repo, ProfileContextRepository)
    repo.save_context("profile", {"name": "default"})
    assert repo.load_context("profile") == {"name": "default"}


def test_in_memory_project_context_repository_contract() -> None:
    repo = TestOnlyInMemoryProjectContextRepository()

    assert isinstance(repo, ProjectContextRepository)
    repo.save_context("project-a", "handoff", {"status": "active"})
    assert repo.load_context("project-a", "handoff") == {"status": "active"}
    assert repo.load_context("project-b", "handoff") is None


def test_test_repository_bundle_groups_all_phase1_contracts() -> None:
    bundle = build_test_repository_bundle(profile_id="default")

    assert isinstance(bundle, RepositoryBundle)
    assert isinstance(bundle.candidates, CandidateRepository)
    assert isinstance(bundle.review_decisions, ReviewDecisionRepository)
    assert isinstance(bundle.lineage, LineageRepository)
    assert isinstance(bundle.profile_context, ProfileContextRepository)
    assert isinstance(bundle.project_context, ProjectContextRepository)

    candidate = _candidate()
    decision = _decision(candidate.id)
    lineage_id = bundle.lineage.append(
        "candidate_reviewed",
        {"candidate_id": candidate.id},
    )

    assert bundle.candidates.save(candidate) == candidate.id
    assert bundle.candidates.load(candidate.id) == candidate
    assert bundle.review_decisions.append(decision) == decision.lineage_event_id
    assert bundle.review_decisions.get(decision.lineage_event_id) == decision
    assert bundle.lineage.get(lineage_id)["candidate_id"] == candidate.id

    assert bundle.profile_context is not None
    bundle.profile_context.save_context("profile", {"name": "default"})
    assert bundle.profile_context.load_context("profile") == {"name": "default"}

    assert bundle.project_context is not None
    bundle.project_context.save_context("project-a", "handoff", {"status": "active"})
    assert bundle.project_context.load_context("project-a", "handoff") == {
        "status": "active",
    }


def test_review_decision_payload_is_json_like() -> None:
    decision = _decision()

    assert review_decision_to_payload(decision)["candidate_id"] == "candidate-1"
    assert review_decision_to_payload(decision)["decision"] == "approve"


def test_vault_bundle_stores_satisfy_repository_contracts() -> None:
    keychain = TestOnlyKeychainProvider()
    crypto = TestOnlyCryptoProvider()
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    bundle = build_vault_repository_bundle(vault, profile_id="default")
    session = keychain.unlock(
        "repository-contract-test",
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

    assert isinstance(bundle.candidates, CandidateRepository)
    assert isinstance(bundle.review_decisions, ReviewDecisionRepository)
    assert isinstance(bundle.lineage, LineageRepository)

    candidate = _candidate()
    decision = _decision(candidate.id)
    lineage_id = bundle.lineage.append(
        "candidate_created",
        {"candidate_id": candidate.id},
        session=session,
    )

    assert bundle.candidates.save(candidate, session=session) == candidate.id
    assert bundle.candidates.load(candidate.id, session=session) == candidate
    assert bundle.review_decisions.append(decision, session=session) == decision.lineage_event_id
    assert bundle.review_decisions.get(decision.lineage_event_id, session=session) == decision
    assert bundle.lineage.get(lineage_id, session=session)["candidate_id"] == candidate.id
