"""Tests for explicit development Local Vault runtime."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.review_decision import ReviewDecision
from sayane.vault.contracts import VaultStoreMode
from sayane.vault.development import build_sqlite_development_vault_runtime
from sayane.vault.unlock_policy import UnlockLevel


def _candidate(candidate_id: str = "c-dev") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="development candidate",
        source=CandidateSource(type="test", uri=None, captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=["development candidate"]),
    )


def _session(runtime, purpose: str):
    opener = getattr(runtime.session_manager, "open_policy_session")
    return opener(purpose, UnlockLevel.SENSITIVE)


def test_development_runtime_encrypts_records_and_persists_keyring(tmp_path) -> None:
    db_path = tmp_path / "vault.sqlite"
    runtime = build_sqlite_development_vault_runtime(
        path=db_path,
        passphrase="dev-passphrase",
        profile_id="default",
    )
    session = _session(runtime, "development-runtime-test")

    runtime.repositories.candidates.save(_candidate(), session=session)
    runtime.repositories.review_decisions.append(
        ReviewDecision(candidate_id="c-dev", decision="approve", reason="ok"),
        session=session,
    )

    assert runtime.mode == VaultStoreMode.DEVELOPMENT
    assert runtime.vault.mode() == VaultStoreMode.DEVELOPMENT

    connection = sqlite3.connect(db_path)
    try:
        keyring_rows = connection.execute("SELECT key_id, data_class, status FROM keyring").fetchall()
        record_rows = connection.execute(
            "SELECT key_id, ciphertext FROM encrypted_records WHERE data_class = 'candidate'"
        ).fetchall()
    finally:
        connection.close()

    assert keyring_rows
    assert any(row[1] == "candidate" for row in keyring_rows)
    assert record_rows
    assert b"development candidate" not in record_rows[0][1]


def test_development_runtime_reloads_encrypted_records_with_same_passphrase(tmp_path) -> None:
    db_path = tmp_path / "vault.sqlite"
    first = build_sqlite_development_vault_runtime(
        path=db_path,
        passphrase="dev-passphrase",
        profile_id="default",
    )
    first_session = _session(first, "first")
    first.repositories.candidates.save(_candidate("c-dev-reload"), session=first_session)
    first.lock(first_session.session_id)

    second = build_sqlite_development_vault_runtime(
        path=db_path,
        passphrase="dev-passphrase",
        profile_id="default",
    )
    second_session = _session(second, "second")
    candidate = second.repositories.candidates.load("c-dev-reload", session=second_session)

    assert candidate is not None
    assert candidate.content == "development candidate"
