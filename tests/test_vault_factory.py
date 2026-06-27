"""Tests for guarded VaultRuntime factory."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.core.candidate import CandidateProposal, CandidateSource, CandidateUpdate
from sayane.core.review_decision import ReviewDecision
from sayane.vault.contracts import VaultStoreError, VaultStoreMode
from sayane.vault.factory import build_test_vault_runtime, open_vault_runtime


def _candidate(candidate_id: str = "c-runtime") -> CandidateUpdate:
    return CandidateUpdate(
        id=candidate_id,
        status="pending",
        target_profile_id="default",
        content="candidate content",
        source=CandidateSource(type="test", uri=None, captured_at=datetime.now(UTC)),
        proposal=CandidateProposal(section="knowledge.concepts", add=["candidate content"]),
    )


def test_open_vault_runtime_requires_explicit_test_mode() -> None:
    with pytest.raises(VaultStoreError, match="production Local Vault backend is not implemented"):
        open_vault_runtime()

    with pytest.raises(VaultStoreError, match="requires explicit sqlite_path"):
        open_vault_runtime(mode="development")


def test_open_vault_runtime_test_mode_builds_test_runtime() -> None:
    runtime = open_vault_runtime(mode="test", profile_id="default")
    assert runtime.mode == VaultStoreMode.TEST
    assert runtime.profile_id == "default"
    assert runtime.keychain.capabilities().assurance.value == "test_only"
    assert runtime.vault.mode() == VaultStoreMode.TEST


def test_open_vault_runtime_development_mode_requires_passphrase(tmp_path) -> None:
    with pytest.raises(VaultStoreError, match="requires explicit passphrase"):
        open_vault_runtime(
            mode="development",
            profile_id="default",
            sqlite_path=tmp_path / "vault.sqlite",
        )


def test_open_vault_runtime_development_mode_builds_explicit_runtime(tmp_path) -> None:
    runtime = open_vault_runtime(
        mode="development",
        profile_id="default",
        sqlite_path=tmp_path / "vault.sqlite",
        passphrase="dev-passphrase",
    )
    assert runtime.mode == VaultStoreMode.DEVELOPMENT
    assert runtime.keychain.capabilities().assurance.value == "passphrase"
    assert runtime.vault.mode() == VaultStoreMode.DEVELOPMENT


def test_vault_runtime_uses_session_manager() -> None:
    runtime = build_test_vault_runtime(profile_id="default")
    session = runtime.unlock("factory-test", ["candidate:read"])

    assert runtime.require_scope(session.session_id, "candidate:read") == session
    with pytest.raises(VaultStoreError, match="missing scope"):
        runtime.require_scope(session.session_id, "candidate:write")

    runtime.lock(session.session_id)
    with pytest.raises(VaultStoreError, match="not found"):
        runtime.require_scope(session.session_id, "candidate:read")


def test_test_vault_runtime_bundle_round_trip() -> None:
    runtime = build_test_vault_runtime(profile_id="default")
    session = runtime.unlock(
        "factory-test",
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

    runtime.repositories.candidates.save(_candidate(), session=session)
    runtime.repositories.review_decisions.append(
        ReviewDecision(candidate_id="c-runtime", decision="approve", reason="ok"),
        session=session,
    )
    runtime.repositories.lineage.append(
        "candidate_approved",
        {"candidate_id": "c-runtime", "operation": "candidate_approved"},
        session=session,
    )

    assert runtime.repositories.smoke_check(session=session) == {
        "profile_id": "default",
        "candidate_count": 1,
        "review_decision_count": 1,
        "lineage_count": 1,
    }


def test_production_runtime_rejects_test_only_components_if_misconfigured() -> None:
    runtime = build_test_vault_runtime(profile_id="default")
    forged = type(runtime)(
        mode=VaultStoreMode.PRODUCTION,
        profile_id=runtime.profile_id,
        keychain=runtime.keychain,
        session_manager=runtime.session_manager,
        vault=runtime.vault,
        repositories=runtime.repositories,
    )

    with pytest.raises(VaultStoreError, match="test-only keychain"):
        forged.require_not_test_only_for_production()
