"""Interface contracts for Sayane encrypted local storage.

These contracts implement the architectural boundary described in
ADR 0001: Local Vault Key Management.

They intentionally do not provide a production plaintext store. Concrete
implementations must make their assurance level explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class DataClass(str, Enum):
    """Logical encryption boundary for Sayane data."""

    PROFILE = "profile"
    PROJECT_CONTEXT = "project_context"
    CANDIDATE = "candidate"
    REVIEW_DECISION = "review_decision"
    LINEAGE = "lineage"
    RAW_CAPTURE = "raw_capture"
    CLOUD_TRANSFER_LOG = "cloud_transfer_log"
    MCP_PREVIEW = "mcp_preview"
    EXPORT = "export"
    DEEP_PRIVATE = "deep_private"


class SecretStoreAssurance(str, Enum):
    """Assurance level of the key release backend."""

    OS_BACKED = "os_backed"
    OS_BACKED_BIOMETRIC = "os_backed_biometric"
    PASSPHRASE = "passphrase"
    LOWER_ASSURANCE = "lower_assurance"
    TEST_ONLY = "test_only"


class VaultStoreMode(str, Enum):
    """Runtime mode of a vault store implementation."""

    PRODUCTION = "production"
    DEVELOPMENT = "development"
    TEST = "test"


@dataclass(frozen=True)
class KeyCapabilities:
    """Capabilities reported by a PlatformKeychainProvider."""

    platform_name: str
    assurance: SecretStoreAssurance
    supports_biometric_unlock: bool = False
    supports_os_password_unlock: bool = False
    supports_secure_enclave: bool = False
    supports_key_rotation: bool = True
    is_headless: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class UnlockSession:
    """Scoped and time-limited vault unlock session."""

    session_id: str
    purpose: str
    scopes: tuple[str, ...]
    assurance: SecretStoreAssurance
    unlocked_at: datetime
    expires_at: datetime
    idle_expires_at: datetime | None = None

    def is_expired(self, *, now: datetime | None = None) -> bool:
        current = now or datetime.now(UTC)
        if current >= self.expires_at:
            return True
        if self.idle_expires_at is not None and current >= self.idle_expires_at:
            return True
        return False

    def allows(self, scope: str) -> bool:
        return scope in self.scopes or "*" in self.scopes


@dataclass(frozen=True)
class KeyMaterial:
    """Opaque key material returned by a key manager.

    Implementations should avoid keeping this object alive longer than the
    active UnlockSession requires.
    """

    key_id: str
    data_class: DataClass
    material: bytes
    created_at: datetime
    expires_at: datetime | None = None


@dataclass(frozen=True)
class KeyringEntry:
    """Metadata for a wrapped data encryption key."""

    key_id: str
    data_class: DataClass
    wrapped_dek: bytes
    wrapping_key_id: str
    algorithm: str
    created_at: datetime
    rotated_at: datetime | None = None
    status: str = "active"


@dataclass(frozen=True)
class EncryptedRecord:
    """Encrypted payload with integrity-bound metadata."""

    record_id: str
    data_class: DataClass
    key_id: str
    nonce: bytes
    ciphertext: bytes
    aad: dict[str, Any]
    created_at: datetime
    algorithm: str


class VaultStoreError(RuntimeError):
    """Base error for Local Vault operations."""


@runtime_checkable
class PlatformKeychainProvider(Protocol):
    """OS-specific secret release abstraction.

    Implementations may use macOS Keychain, Windows DPAPI / Hello, Linux
    Secret Service, or explicit passphrase fallback. Callers must not depend on
    platform-specific APIs above this interface.
    """

    def platform_name(self) -> str:
        """Return implementation platform name."""
        ...

    def capabilities(self) -> KeyCapabilities:
        """Return OS keychain capability and assurance information."""
        ...

    def get_or_create_wrapping_secret(self, key_id: str) -> bytes:
        """Return an OS-protected wrapping secret for the given key id."""
        ...

    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession:
        """Request an OS-backed or fallback unlock session."""
        ...

    def lock(self, session_id: str) -> None:
        """End an unlock session and release related key material."""
        ...

    def rotate_wrapping_secret(self, key_id: str) -> None:
        """Rotate or reissue the platform wrapping secret."""
        ...


@runtime_checkable
class UnlockSessionManager(Protocol):
    """Manage scoped unlock sessions."""

    def open_session(self, purpose: str, scopes: list[str]) -> UnlockSession:
        """Open a new scoped unlock session."""
        ...

    def require_scope(self, session_id: str, scope: str) -> UnlockSession:
        """Return a valid session or raise when missing/expired/insufficient."""
        ...

    def close_session(self, session_id: str) -> None:
        """Close a session and clear cached key material."""
        ...


@runtime_checkable
class KeyManager(Protocol):
    """Envelope key manager.

    The master KEK or wrapping secret must wrap DEKs. It must not directly
    encrypt arbitrary application records.
    """

    def get_or_create_dek(
        self,
        data_class: DataClass,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        """Return DEK material for a data class under a valid session."""
        ...

    def wrap_dek(self, data_class: DataClass, dek: bytes) -> KeyringEntry:
        """Wrap a DEK into a KeyringEntry."""
        ...

    def unwrap_dek(
        self,
        entry: KeyringEntry,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        """Unwrap a DEK using the platform-backed wrapping secret."""
        ...

    def rotate_dek(self, data_class: DataClass) -> KeyringEntry:
        """Create a rotated DEK for a data class."""
        ...

    def destroy_dek(self, data_class: DataClass) -> None:
        """Destroy a DEK when retention or Right to Fade requires it."""
        ...


@runtime_checkable
class CryptoProvider(Protocol):
    """Authenticated encryption provider."""

    def encrypt_record(
        self,
        *,
        record_id: str,
        data_class: DataClass,
        plaintext: bytes,
        aad: dict[str, Any],
        session: UnlockSession,
    ) -> EncryptedRecord:
        """Encrypt one record with data-class DEK and AAD binding."""
        ...

    def decrypt_record(
        self,
        record: EncryptedRecord,
        *,
        session: UnlockSession,
    ) -> bytes:
        """Decrypt one record after session and AAD integrity checks."""
        ...


@runtime_checkable
class VaultStore(Protocol):
    """Encrypted local record store contract."""

    def mode(self) -> VaultStoreMode:
        """Return production/development/test mode."""
        ...

    def is_plaintext_default(self) -> bool:
        """Return True only for explicit non-production test stores."""
        ...

    def put(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        plaintext: bytes,
        aad: dict[str, Any],
        session: UnlockSession,
    ) -> EncryptedRecord:
        """Persist encrypted record content."""
        ...

    def get(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> bytes | None:
        """Read and decrypt one record, if present."""
        ...

    def delete(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> None:
        """Delete one encrypted record."""
        ...

    def list_record_ids(self, data_class: DataClass) -> list[str]:
        """List record ids without exposing plaintext."""
        ...


def assert_vault_store_safe_for_production(store: VaultStore) -> None:
    """Reject plaintext or test-only vault stores in production mode."""
    if store.mode() == VaultStoreMode.PRODUCTION and store.is_plaintext_default():
        raise VaultStoreError("plaintext vault store cannot be production default")
