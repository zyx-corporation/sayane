"""Local Vault runtime factory.

This module is the controlled construction point for Vault-backed repository
bundles. It prevents test-only vault components from becoming production
defaults while production Local Vault backends are still unimplemented.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from sayane.storage.vault_bundle import VaultRepositoryBundle, build_vault_repository_bundle
from sayane.vault.contracts import (
    PlatformKeychainProvider,
    UnlockSession,
    UnlockSessionManager,
    VaultStore,
    VaultStoreError,
    VaultStoreMode,
)
from sayane.vault.session import InMemoryUnlockSessionManager
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import (
    CryptoBackedInMemoryTestVaultStore,
    TestOnlyKeychainProvider,
)
from sayane.vault.unlock_policy import UnlockLevel

VaultRuntimeMode = Literal["production", "development", "test"]


@dataclass(frozen=True)
class VaultRuntime:
    """Constructed Local Vault runtime for one profile."""

    mode: VaultStoreMode
    profile_id: str
    keychain: PlatformKeychainProvider
    session_manager: UnlockSessionManager
    vault: VaultStore
    repositories: VaultRepositoryBundle

    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession:
        """Open a scoped unlock session through the runtime session manager."""
        return self.session_manager.open_session(purpose, scopes)

    def require_scope(self, session_id: str, scope: str) -> UnlockSession:
        """Require a valid scoped session through the runtime session manager."""
        return self.session_manager.require_scope(session_id, scope)

    def lock(self, session_id: str) -> None:
        """Close one unlock session."""
        self.session_manager.close_session(session_id)

    def open_policy_session(self, purpose: str, level: UnlockLevel) -> UnlockSession:
        """Open a policy-based session when supported by the session manager."""
        opener = getattr(self.session_manager, "open_policy_session", None)
        if opener is None:
            raise VaultStoreError("policy-based unlock sessions are not supported by this runtime")
        return opener(purpose, level)

    def require_not_test_only_for_production(self) -> None:
        """Raise if a production runtime uses a test-only keychain or store."""
        if self.mode != VaultStoreMode.PRODUCTION:
            return
        caps = self.keychain.capabilities()
        if caps.assurance.value == "test_only":
            raise VaultStoreError("test-only keychain cannot be production runtime")
        if self.vault.mode() == VaultStoreMode.TEST:
            raise VaultStoreError("test-only vault store cannot be production runtime")
        self.repositories.require_safe_for_production()


def build_test_vault_runtime(*, profile_id: str = "default") -> VaultRuntime:
    """Build an explicit test-only VaultRuntime.

    This is allowed only for tests and local contract validation. It must never
    be used as a production default.
    """
    keychain = TestOnlyKeychainProvider()
    session_manager = InMemoryUnlockSessionManager(keychain)
    key_manager = TestOnlyKeyManager(keychain=keychain)
    crypto = TestOnlyCryptoProvider(key_manager=key_manager)
    vault = CryptoBackedInMemoryTestVaultStore(crypto=crypto)
    repositories = build_vault_repository_bundle(vault, profile_id=profile_id)
    return VaultRuntime(
        mode=VaultStoreMode.TEST,
        profile_id=profile_id,
        keychain=keychain,
        session_manager=session_manager,
        vault=vault,
        repositories=repositories,
    )


def open_vault_runtime(
    *,
    mode: VaultRuntimeMode = "production",
    profile_id: str = "default",
    sqlite_path: Path | None = None,
    passphrase: str | None = None,
) -> VaultRuntime:
    """Open a VaultRuntime.

    Production and development backends are intentionally not implemented yet.
    Callers must explicitly request mode="test" to obtain test-only components.
    """
    if mode == "test":
        return build_test_vault_runtime(profile_id=profile_id)
    if mode == "development":
        if sqlite_path is None:
            raise VaultStoreError("development Local Vault backend requires explicit sqlite_path")
        if not passphrase:
            raise VaultStoreError("development Local Vault backend requires explicit passphrase")
        from sayane.vault.development import build_sqlite_development_vault_runtime

        return build_sqlite_development_vault_runtime(
            path=sqlite_path,
            passphrase=passphrase,
            profile_id=profile_id,
        )
    raise VaultStoreError("production Local Vault backend is not implemented")
