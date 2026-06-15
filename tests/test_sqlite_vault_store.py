"""Tests for SQLite-backed Local Vault store."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Any

import pytest

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.mcp_context import build_compiled_context
from sayane.core.review_decision import (
    ReviewDecision,
    clear_decisions,
    load_review_decisions,
    save_decision,
    set_review_decision_repository,
)
from sayane.vault.contracts import DataClass, UnlockSession, VaultStoreError, VaultStoreMode
from sayane.vault.sqlite_runtime import build_sqlite_test_vault_runtime
from sayane.vault.sqlite_schema import inspect_sqlite_tables, validate_sqlite_vault_schema
from sayane.vault.sqlite_store import SQLiteVaultStore
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import TestOnlyKeychainProvider


class SessionBoundReviewDecisionRepository:
    """Bind a VaultReviewDecisionStore to one UnlockSession for seam tests."""

    def __init__(self, repository, session: UnlockSession) -> None:
        self._repository = repository
        self._session = session

    def append(self, decision: ReviewDecision, **kwargs: Any) -> str:
        _ = kwargs
        return self._repository.append(decision, session=self._session)

    def list(self, **kwargs: Any) -> list[ReviewDecision]:
        _ = kwargs
        return self._repository.list(session=self._session)

    def get(self, record_id: str, **kwargs: Any) -> ReviewDecision | None:
        _ = kwargs
        return self._repository.get(record_id, session=self._session)


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


def _runtime_session(runtime, purpose: str):
    return runtime.keychain.unlock(
        purpose,
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
    assert store.get(data_class=DataClass.CANDIDATE, record_id="c1", session=session) is None


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
    session = _runtime_session(runtime, "sqlite-runtime-bundle-test")

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


def test_sqlite_test_runtime_reloads_repository_records(tmp_path) -> None:
    path = tmp_path / "vault.sqlite"
    first = build_sqlite_test_vault_runtime(path=path, profile_id="default")
    first_session = _runtime_session(first, "sqlite-runtime-first")

    candidate = _candidate("c-sqlite-reload")
    decision = ReviewDecision(
        candidate_id=candidate.id,
        decision="approve",
        reason="Accepted before reload.",
        applied_value="Persistent review decision.",
        original_section="project.context",
    )
    lineage_payload = {"candidate_id": candidate.id, "operation": "candidate_approved"}

    first.repositories.candidates.save(candidate, session=first_session)
    first.repositories.review_decisions.append(decision, session=first_session)
    lineage_id = first.repositories.lineage.append(
        "candidate_approved",
        lineage_payload,
        session=first_session,
    )

    second = build_sqlite_test_vault_runtime(path=path, profile_id="default")
    second_session = _runtime_session(second, "sqlite-runtime-second")

    assert second.repositories.candidates.load(candidate.id, session=second_session) == candidate
    assert second.repositories.review_decisions.get(
        decision.lineage_event_id,
        session=second_session,
    ) == decision
    assert second.repositories.lineage.get(lineage_id, session=second_session)["candidate_id"] == (
        candidate.id
    )


def test_sqlite_repository_review_decisions_feed_mcp_context(tmp_path) -> None:
    profile_id = "sqlite-mcp"
    clear_decisions(profile_id)
    runtime = build_sqlite_test_vault_runtime(
        path=tmp_path / "vault.sqlite",
        profile_id=profile_id,
    )
    session = _runtime_session(runtime, "sqlite-mcp")
    repository = SessionBoundReviewDecisionRepository(
        runtime.repositories.review_decisions,
        session,
    )
    decision = ReviewDecision(
        candidate_id="c-sqlite-mcp",
        decision="approve",
        reason="Accepted through SQLite repository.",
        applied_value="SQLite-backed context for MCP.",
        original_section="project.context",
    )

    repository.append(decision)
    set_review_decision_repository(profile_id, repository)

    compiled = build_compiled_context(
        profile_id=profile_id,
        mode="full",
        scoped_decisions=load_review_decisions(profile_id, project_id="project-a"),
    )

    assert compiled["included_approved_candidates"][0]["candidate_id"] == "c-sqlite-mcp"
    assert compiled["included_approved_candidates"][0]["content"] == (
        "SQLite-backed context for MCP."
    )

    clear_decisions(profile_id)


def test_save_decision_can_write_through_sqlite_repository_seam(tmp_path) -> None:
    profile_id = "sqlite-save-seam"
    clear_decisions(profile_id)
    runtime = build_sqlite_test_vault_runtime(
        path=tmp_path / "vault.sqlite",
        profile_id=profile_id,
    )
    session = _runtime_session(runtime, "sqlite-save-seam")
    repository = SessionBoundReviewDecisionRepository(
        runtime.repositories.review_decisions,
        session,
    )
    set_review_decision_repository(profile_id, repository)
    decision = ReviewDecision(
        candidate_id="c-sqlite-save-seam",
        decision="approve",
        reason="Accepted through save_decision seam.",
    )

    save_decision(profile_id, decision)

    assert runtime.repositories.review_decisions.get(
        decision.lineage_event_id,
        session=session,
    ) == decision
    assert load_review_decisions(profile_id) == [decision]

    clear_decisions(profile_id)
