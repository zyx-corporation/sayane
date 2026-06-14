"""Test-only in-memory Local Vault implementation.

This module is intentionally not a production vault. It exists so contract tests
and future repository adapters can exercise the VaultStore interface without
requiring OS keychain integration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sayane.vault.contracts import (
    CryptoProvider,
    DataClass,
    EncryptedRecord,
    KeyCapabilities,
    PlatformKeychainProvider,
    SecretStoreAssurance,
    UnlockSession,
    VaultStore,
    VaultStoreError,
    VaultStoreMode,
)


@dataclass
class TestOnlyKeychainProvider(PlatformKeychainProvider):
    """Deterministic test-only keychain provider.

    This provider must never be selected by production defaults.
    """

    wrapping_secret: bytes = b"sayane-test-wrapping-secret"
    active_sessions: dict[str, UnlockSession] = field(default_factory=dict)

    def platform_name(self) -> str:
        return "test-only"

    def capabilities(self) -> KeyCapabilities:
        return KeyCapabilities(
            platform_name=self.platform_name(),
            assurance=SecretStoreAssurance.TEST_ONLY,
            supports_biometric_unlock=False,
            supports_os_password_unlock=False,
            supports_secure_enclave=False,
            supports_key_rotation=False,
            notes=["test-only provider; never production"],
        )

    def get_or_create_wrapping_secret(self, key_id: str) -> bytes:
        _ = key_id
        return self.wrapping_secret

    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession:
        now = datetime.now(UTC)
        session = UnlockSession(
            session_id=uuid4().hex,
            purpose=purpose,
            scopes=tuple(scopes),
            assurance=SecretStoreAssurance.TEST_ONLY,
            unlocked_at=now,
            expires_at=now + timedelta(minutes=5),
        )
        self.active_sessions[session.session_id] = session
        return session

    def lock(self, session_id: str) -> None:
        self.active_sessions.pop(session_id, None)

    def rotate_wrapping_secret(self, key_id: str) -> None:
        _ = key_id
        raise VaultStoreError("test-only keychain does not support rotation")


@dataclass
class InMemoryTestVaultStore(VaultStore):
    """In-memory test vault.

    Records are stored as EncryptedRecord objects, but ciphertext is only tagged
    and reversed for test determinism. This is not cryptographic protection.
    """

    records: dict[tuple[DataClass, str], EncryptedRecord] = field(default_factory=dict)

    def mode(self) -> VaultStoreMode:
        return VaultStoreMode.TEST

    def is_plaintext_default(self) -> bool:
        return True

    def put(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        plaintext: bytes,
        aad: dict,
        session: UnlockSession,
    ) -> EncryptedRecord:
        _require_session(session, f"{data_class.value}:write")
        record = EncryptedRecord(
            record_id=record_id,
            data_class=data_class,
            key_id=f"test-{data_class.value}",
            nonce=b"test-nonce",
            ciphertext=_test_encrypt(plaintext),
            aad=dict(aad),
            created_at=datetime.now(UTC),
            algorithm="test-only-reverse-bytes",
        )
        self.records[(data_class, record_id)] = record
        return record

    def get(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> bytes | None:
        _require_session(session, f"{data_class.value}:read")
        record = self.records.get((data_class, record_id))
        if record is None:
            return None
        return _test_decrypt(record.ciphertext)

    def delete(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> None:
        _require_session(session, f"{data_class.value}:delete")
        self.records.pop((data_class, record_id), None)

    def list_record_ids(self, data_class: DataClass, *, session: UnlockSession) -> list[str]:
        _require_session(session, f"{data_class.value}:read")
        return sorted(record_id for dc, record_id in self.records if dc == data_class)


@dataclass
class CryptoBackedInMemoryTestVaultStore(VaultStore):
    """In-memory test vault that routes encryption through CryptoProvider."""

    crypto: CryptoProvider
    records: dict[tuple[DataClass, str], EncryptedRecord] = field(default_factory=dict)

    def mode(self) -> VaultStoreMode:
        return VaultStoreMode.TEST

    def is_plaintext_default(self) -> bool:
        return False

    def put(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        plaintext: bytes,
        aad: dict,
        session: UnlockSession,
    ) -> EncryptedRecord:
        _require_session(session, f"{data_class.value}:write")
        record = self.crypto.encrypt_record(
            record_id=record_id,
            data_class=data_class,
            plaintext=plaintext,
            aad=aad,
            session=session,
        )
        self.records[(data_class, record_id)] = record
        return record

    def get(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> bytes | None:
        _require_session(session, f"{data_class.value}:read")
        record = self.records.get((data_class, record_id))
        if record is None:
            return None
        return self.crypto.decrypt_record(record, session=session)

    def delete(
        self,
        *,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> None:
        _require_session(session, f"{data_class.value}:delete")
        self.records.pop((data_class, record_id), None)

    def list_record_ids(self, data_class: DataClass, *, session: UnlockSession) -> list[str]:
        _require_session(session, f"{data_class.value}:read")
        return sorted(record_id for dc, record_id in self.records if dc == data_class)


def _require_session(session: UnlockSession, scope: str) -> None:
    if session.is_expired():
        raise VaultStoreError("unlock session expired")
    if not session.allows(scope):
        raise VaultStoreError(f"unlock session missing scope: {scope}")


def _test_encrypt(plaintext: bytes) -> bytes:
    return b"TESTONLY:" + plaintext[::-1]


def _test_decrypt(ciphertext: bytes) -> bytes:
    prefix = b"TESTONLY:"
    if not ciphertext.startswith(prefix):
        raise VaultStoreError("invalid test ciphertext")
    return ciphertext[len(prefix):][::-1]
