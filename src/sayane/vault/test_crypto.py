"""Test-only KeyManager and CryptoProvider implementations.

These implementations exercise the Local Vault contracts without providing
production cryptography. They must never be selected by production defaults.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from sayane.vault.contracts import (
    CryptoProvider,
    DataClass,
    EncryptedRecord,
    KeyManager,
    KeyMaterial,
    KeyringEntry,
    UnlockSession,
    VaultStoreError,
)
from sayane.vault.test_store import TestOnlyKeychainProvider


@dataclass
class TestOnlyKeyManager(KeyManager):
    """Envelope KeyManager for tests only.

    DEKs are deterministic per data class to keep tests stable. This is not
    cryptographic key generation.
    """

    keychain: TestOnlyKeychainProvider = field(default_factory=TestOnlyKeychainProvider)
    keyring: dict[DataClass, KeyringEntry] = field(default_factory=dict)

    def get_or_create_dek(
        self,
        data_class: DataClass,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        _require_scope(session, f"{data_class.value}:key")
        entry = self.keyring.get(data_class)
        if entry is None:
            raw = self._derive_test_dek(data_class, version="v1")
            entry = self.wrap_dek(data_class, raw)
            self.keyring[data_class] = entry
        return self.unwrap_dek(entry, session=session)

    def wrap_dek(self, data_class: DataClass, dek: bytes) -> KeyringEntry:
        secret = self.keychain.get_or_create_wrapping_secret("test-wrapping-key")
        wrapped = _xor_with_digest(dek, secret)
        return KeyringEntry(
            key_id=f"test-{data_class.value}-dek",
            data_class=data_class,
            wrapped_dek=wrapped,
            wrapping_key_id="test-wrapping-key",
            algorithm="test-only-xor-with-digest",
            created_at=datetime.now(UTC),
        )

    def unwrap_dek(
        self,
        entry: KeyringEntry,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        _require_scope(session, f"{entry.data_class.value}:key")
        secret = self.keychain.get_or_create_wrapping_secret(entry.wrapping_key_id)
        raw = _xor_with_digest(entry.wrapped_dek, secret)
        return KeyMaterial(
            key_id=entry.key_id,
            data_class=entry.data_class,
            material=raw,
            created_at=entry.created_at,
            expires_at=session.expires_at,
        )

    def rotate_dek(self, data_class: DataClass) -> KeyringEntry:
        raw = self._derive_test_dek(data_class, version=f"v{len(self.keyring) + 2}")
        entry = self.wrap_dek(data_class, raw)
        entry = KeyringEntry(
            key_id=f"{entry.key_id}-rotated-{len(self.keyring) + 1}",
            data_class=entry.data_class,
            wrapped_dek=entry.wrapped_dek,
            wrapping_key_id=entry.wrapping_key_id,
            algorithm=entry.algorithm,
            created_at=entry.created_at,
            rotated_at=datetime.now(UTC),
            status=entry.status,
        )
        self.keyring[data_class] = entry
        return entry

    def destroy_dek(self, data_class: DataClass) -> None:
        self.keyring.pop(data_class, None)

    def _derive_test_dek(self, data_class: DataClass, *, version: str) -> bytes:
        return hashlib.sha256(f"sayane-test-dek:{data_class.value}:{version}".encode()).digest()


@dataclass
class TestOnlyCryptoProvider(CryptoProvider):
    """Authenticated-encryption-shaped test provider.

    This provider binds ciphertext to AAD by hashing AAD into the test payload.
    It is deterministic and not secure.
    """

    key_manager: TestOnlyKeyManager = field(default_factory=TestOnlyKeyManager)

    def encrypt_record(
        self,
        *,
        record_id: str,
        data_class: DataClass,
        plaintext: bytes,
        aad: dict,
        session: UnlockSession,
    ) -> EncryptedRecord:
        key = self.key_manager.get_or_create_dek(data_class, session=session)
        aad_digest = _aad_digest(aad)
        ciphertext = _xor_with_digest(plaintext + aad_digest, key.material)
        return EncryptedRecord(
            record_id=record_id,
            data_class=data_class,
            key_id=key.key_id,
            nonce=b"test-nonce",
            ciphertext=ciphertext,
            aad=dict(aad),
            created_at=datetime.now(UTC),
            algorithm="test-only-aad-bound-xor",
        )

    def decrypt_record(
        self,
        record: EncryptedRecord,
        *,
        session: UnlockSession,
    ) -> bytes:
        entry = self.key_manager.keyring.get(record.data_class)
        if entry is None:
            self.key_manager.get_or_create_dek(record.data_class, session=session)
            entry = self.key_manager.keyring.get(record.data_class)
        if entry is None or entry.key_id != record.key_id:
            raise VaultStoreError("missing matching test key for encrypted record")
        key = self.key_manager.unwrap_dek(entry, session=session)
        payload = _xor_with_digest(record.ciphertext, key.material)
        aad_digest = _aad_digest(record.aad)
        if not payload.endswith(aad_digest):
            raise VaultStoreError("AAD integrity check failed")
        return payload[: -len(aad_digest)]


def _require_scope(session: UnlockSession, scope: str) -> None:
    if session.is_expired():
        raise VaultStoreError("unlock session expired")
    if not session.allows(scope) and not session.allows("vault:key"):
        raise VaultStoreError(f"unlock session missing scope: {scope}")


def _xor_with_digest(data: bytes, seed: bytes) -> bytes:
    stream = hashlib.sha256(seed).digest()
    repeated = (stream * ((len(data) // len(stream)) + 1))[: len(data)]
    return bytes(a ^ b for a, b in zip(data, repeated, strict=True))


def _aad_digest(aad: dict) -> bytes:
    canonical = repr(sorted(aad.items())).encode("utf-8")
    return hashlib.sha256(canonical).digest()[:16]
