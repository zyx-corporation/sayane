"""Local Vault abstractions for Sayane.

The vault package defines contracts for encrypted local storage. Concrete
production backends must use OS-backed key release and envelope encryption;
test backends must remain explicitly test-only.
"""

from sayane.vault.contracts import (
    CryptoProvider,
    DataClass,
    EncryptedRecord,
    KeyCapabilities,
    KeyManager,
    KeyMaterial,
    KeyringEntry,
    PlatformKeychainProvider,
    SecretStoreAssurance,
    UnlockSession,
    UnlockSessionManager,
    VaultStore,
    VaultStoreError,
    VaultStoreMode,
)

__all__ = [
    "CryptoProvider",
    "DataClass",
    "EncryptedRecord",
    "KeyCapabilities",
    "KeyManager",
    "KeyMaterial",
    "KeyringEntry",
    "PlatformKeychainProvider",
    "SecretStoreAssurance",
    "UnlockSession",
    "UnlockSessionManager",
    "VaultStore",
    "VaultStoreError",
    "VaultStoreMode",
]
