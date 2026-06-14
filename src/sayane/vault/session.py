"""Unlock session management for Local Vault.

The session manager is independent from any concrete production keychain. It
wraps a PlatformKeychainProvider and enforces session existence, timeout, and
scope checks before repositories or vault stores use a session.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sayane.vault.contracts import (
    PlatformKeychainProvider,
    UnlockSession,
    UnlockSessionManager,
    VaultStoreError,
)


@dataclass
class InMemoryUnlockSessionManager(UnlockSessionManager):
    """In-memory scoped unlock session manager.

    This manager does not implement OS authentication by itself. It delegates
    key release to PlatformKeychainProvider and stores only session metadata.
    """

    keychain: PlatformKeychainProvider
    sessions: dict[str, UnlockSession] = field(default_factory=dict)

    def open_session(self, purpose: str, scopes: list[str]) -> UnlockSession:
        """Open and track a new scoped unlock session."""
        session = self.keychain.unlock(purpose, scopes)
        self.sessions[session.session_id] = session
        return session

    def require_scope(self, session_id: str, scope: str) -> UnlockSession:
        """Return a valid session or raise when missing/expired/insufficient."""
        session = self.sessions.get(session_id)
        if session is None:
            raise VaultStoreError("unlock session not found")
        if session.is_expired():
            self.close_session(session_id)
            raise VaultStoreError("unlock session expired")
        if not session.allows(scope):
            raise VaultStoreError(f"unlock session missing scope: {scope}")
        return session

    def close_session(self, session_id: str) -> None:
        """Close a session and ask the keychain to release it as well."""
        self.sessions.pop(session_id, None)
        self.keychain.lock(session_id)

    def close_all(self) -> None:
        """Close all tracked sessions."""
        for session_id in list(self.sessions):
            self.close_session(session_id)
