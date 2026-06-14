"""Explicit SQLite-backed Local Vault runtime builders.

These builders are not production defaults. They are used to exercise the
SQLite persistence seam with explicit test-only crypto/keychain components.
"""

from __future__ import annotations

from pathlib import Path

from sayane.storage.vault_bundle import build_vault_repository_bundle
from sayane.vault.contracts import VaultStoreMode
from sayane.vault.factory import VaultRuntime
from sayane.vault.session import InMemoryUnlockSessionManager
from sayane.vault.sqlite_store import SQLiteVaultStore
from sayane.vault.test_crypto import TestOnlyCryptoProvider, TestOnlyKeyManager
from sayane.vault.test_store import TestOnlyKeychainProvider


def build_sqlite_test_vault_runtime(
    *,
    path: Path,
    profile_id: str = "default",
) -> VaultRuntime:
    """Build an explicit test-only VaultRuntime backed by SQLite.

    This uses test-only keychain and crypto components, so it must not become a
    production default. The value is in testing the SQLite persistence seam and
    repository adapters against a durable file.
    """
    keychain = TestOnlyKeychainProvider()
    session_manager = InMemoryUnlockSessionManager(keychain)
    key_manager = TestOnlyKeyManager(keychain=keychain)
    crypto = TestOnlyCryptoProvider(key_manager=key_manager)
    vault = SQLiteVaultStore(path=path, crypto=crypto, store_mode=VaultStoreMode.TEST)
    vault.initialize()
    repositories = build_vault_repository_bundle(vault, profile_id=profile_id)
    return VaultRuntime(
        mode=VaultStoreMode.TEST,
        profile_id=profile_id,
        keychain=keychain,
        session_manager=session_manager,
        vault=vault,
        repositories=repositories,
    )
