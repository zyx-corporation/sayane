"""Tests for Local Vault unlock session manager."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from sayane.vault.contracts import VaultStoreError
from sayane.vault.session import InMemoryUnlockSessionManager
from sayane.vault.test_store import TestOnlyKeychainProvider


def test_unlock_session_manager_opens_and_requires_scope() -> None:
    keychain = TestOnlyKeychainProvider()
    manager = InMemoryUnlockSessionManager(keychain)

    session = manager.open_session("unit-test", ["candidate:read"])
    assert session.session_id in manager.sessions
    assert session.session_id in keychain.active_sessions

    required = manager.require_scope(session.session_id, "candidate:read")
    assert required.session_id == session.session_id


def test_unlock_session_manager_rejects_missing_session() -> None:
    manager = InMemoryUnlockSessionManager(TestOnlyKeychainProvider())

    with pytest.raises(VaultStoreError, match="not found"):
        manager.require_scope("missing", "candidate:read")


def test_unlock_session_manager_rejects_missing_scope() -> None:
    manager = InMemoryUnlockSessionManager(TestOnlyKeychainProvider())
    session = manager.open_session("unit-test", ["candidate:read"])

    with pytest.raises(VaultStoreError, match="missing scope"):
        manager.require_scope(session.session_id, "candidate:write")


def test_unlock_session_manager_expires_and_closes_session() -> None:
    keychain = TestOnlyKeychainProvider()
    manager = InMemoryUnlockSessionManager(keychain)
    session = manager.open_session("unit-test", ["candidate:read"])
    expired = replace(session, expires_at=datetime.now(UTC) - timedelta(seconds=1))
    manager.sessions[session.session_id] = expired

    with pytest.raises(VaultStoreError, match="expired"):
        manager.require_scope(session.session_id, "candidate:read")

    assert session.session_id not in manager.sessions
    assert session.session_id not in keychain.active_sessions


def test_unlock_session_manager_close_all() -> None:
    keychain = TestOnlyKeychainProvider()
    manager = InMemoryUnlockSessionManager(keychain)
    s1 = manager.open_session("unit-test", ["candidate:read"])
    s2 = manager.open_session("unit-test", ["lineage:read"])

    manager.close_all()

    assert manager.sessions == {}
    assert s1.session_id not in keychain.active_sessions
    assert s2.session_id not in keychain.active_sessions
