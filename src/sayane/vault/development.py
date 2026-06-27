"""Explicit lower-assurance Local Vault runtime for development.

This module provides a concrete encrypted SQLite-backed vault using an
explicit passphrase-derived wrapping secret. It is intentionally not a
production default and exists to make ADR 0001's envelope-encryption and
unlock-session boundary executable before OS-backed keychain integrations land.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from sayane.storage.vault_bundle import build_vault_repository_bundle
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
    VaultStoreError,
    VaultStoreMode,
)
from sayane.vault.factory import VaultRuntime
from sayane.vault.session import InMemoryUnlockSessionManager
from sayane.vault.sqlite_store import SQLiteVaultStore


def _canonical_aad(aad: dict[str, object]) -> bytes:
    return json.dumps(aad, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )


def _wrap_with_secret(secret: bytes, plaintext: bytes) -> bytes:
    nonce = os.urandom(12)
    ciphertext = AESGCM(secret).encrypt(nonce, plaintext, None)
    return nonce + ciphertext


def _unwrap_with_secret(secret: bytes, wrapped: bytes) -> bytes:
    if len(wrapped) < 13:
        raise VaultStoreError("wrapped key payload is truncated")
    nonce = wrapped[:12]
    ciphertext = wrapped[12:]
    try:
        return AESGCM(secret).decrypt(nonce, ciphertext, None)
    except Exception as exc:  # pragma: no cover - cryptography error type is backend-specific
        raise VaultStoreError("failed to unwrap data-encryption key") from exc


@dataclass
class PassphraseKeychainProvider(PlatformKeychainProvider):
    """Explicit passphrase-backed key release provider.

    This is a lower-assurance fallback for development and local validation.
    It must never become the implicit production default.
    """

    passphrase: str
    active_sessions: dict[str, UnlockSession] = field(default_factory=dict)

    def platform_name(self) -> str:
        return "explicit-passphrase"

    def capabilities(self) -> KeyCapabilities:
        return KeyCapabilities(
            platform_name=self.platform_name(),
            assurance=SecretStoreAssurance.PASSPHRASE,
            supports_biometric_unlock=False,
            supports_os_password_unlock=False,
            supports_secure_enclave=False,
            supports_key_rotation=True,
            is_headless=False,
            notes=[
                "explicit passphrase fallback",
                "lower assurance than OS-backed keychain",
            ],
        )

    def get_or_create_wrapping_secret(self, key_id: str) -> bytes:
        salt = f"sayane-local-vault:{key_id}".encode("utf-8")
        return hashlib.scrypt(
            self.passphrase.encode("utf-8"),
            salt=salt,
            n=2**14,
            r=8,
            p=1,
            dklen=32,
        )

    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession:
        now = datetime.now(UTC)
        session = UnlockSession(
            session_id=uuid4().hex,
            purpose=purpose,
            scopes=tuple(scopes),
            assurance=SecretStoreAssurance.PASSPHRASE,
            unlocked_at=now,
            expires_at=now + timedelta(minutes=15),
            idle_expires_at=now + timedelta(minutes=5),
        )
        self.active_sessions[session.session_id] = session
        return session

    def lock(self, session_id: str) -> None:
        self.active_sessions.pop(session_id, None)

    def rotate_wrapping_secret(self, key_id: str) -> None:
        _ = key_id
        raise VaultStoreError(
            "passphrase provider uses explicit passphrase rotation outside automatic keychain rotation"
        )


@dataclass
class SQLiteKeyringKeyManager(KeyManager):
    """Envelope key manager backed by the SQLite keyring table."""

    path: Path
    keychain: PlatformKeychainProvider
    wrapping_key_id: str = "local-vault-wrapping-key"

    def get_or_create_dek(
        self,
        data_class: DataClass,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        self._require_scope(session, f"{data_class.value}:key")
        entry = self._load_active_entry(data_class)
        if entry is None:
            entry = self.wrap_dek(data_class, os.urandom(32))
        return self.unwrap_dek(entry, session=session)

    def wrap_dek(self, data_class: DataClass, dek: bytes) -> KeyringEntry:
        secret = self.keychain.get_or_create_wrapping_secret(self.wrapping_key_id)
        wrapped = _wrap_with_secret(secret, dek)
        entry = KeyringEntry(
            key_id=f"{data_class.value}-dek-{uuid4().hex}",
            data_class=data_class,
            wrapped_dek=wrapped,
            wrapping_key_id=self.wrapping_key_id,
            algorithm="AES-256-GCM-wrap",
            created_at=datetime.now(UTC),
            status="active",
        )
        self._persist_entry(entry)
        return entry

    def unwrap_dek(
        self,
        entry: KeyringEntry,
        *,
        session: UnlockSession,
    ) -> KeyMaterial:
        self._require_scope(session, f"{entry.data_class.value}:key")
        secret = self.keychain.get_or_create_wrapping_secret(entry.wrapping_key_id)
        material = _unwrap_with_secret(secret, entry.wrapped_dek)
        return KeyMaterial(
            key_id=entry.key_id,
            data_class=entry.data_class,
            material=material,
            created_at=entry.created_at,
            expires_at=session.expires_at,
        )

    def rotate_dek(self, data_class: DataClass) -> KeyringEntry:
        current = self._load_active_entry(data_class)
        if current is not None:
            self._update_entry_status(current.key_id, "rotated", rotated_at=datetime.now(UTC))
        return self.wrap_dek(data_class, os.urandom(32))

    def destroy_dek(self, data_class: DataClass) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute("DELETE FROM keyring WHERE data_class = ?", (data_class.value,))
            connection.commit()
        finally:
            connection.close()

    def load_entry_for_key_id(self, key_id: str) -> KeyringEntry | None:
        connection = sqlite3.connect(self.path)
        try:
            row = connection.execute(
                """
                SELECT key_id, data_class, wrapped_dek, wrapping_key_id, algorithm, created_at, rotated_at, status
                FROM keyring
                WHERE key_id = ?
                """,
                (key_id,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return KeyringEntry(
            key_id=row[0],
            data_class=DataClass(row[1]),
            wrapped_dek=row[2],
            wrapping_key_id=row[3],
            algorithm=row[4],
            created_at=datetime.fromisoformat(row[5]),
            rotated_at=datetime.fromisoformat(row[6]) if row[6] else None,
            status=row[7],
        )

    def _load_active_entry(self, data_class: DataClass) -> KeyringEntry | None:
        connection = sqlite3.connect(self.path)
        try:
            row = connection.execute(
                """
                SELECT key_id, data_class, wrapped_dek, wrapping_key_id, algorithm, created_at, rotated_at, status
                FROM keyring
                WHERE data_class = ? AND status = 'active'
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (data_class.value,),
            ).fetchone()
        finally:
            connection.close()
        if row is None:
            return None
        return KeyringEntry(
            key_id=row[0],
            data_class=DataClass(row[1]),
            wrapped_dek=row[2],
            wrapping_key_id=row[3],
            algorithm=row[4],
            created_at=datetime.fromisoformat(row[5]),
            rotated_at=datetime.fromisoformat(row[6]) if row[6] else None,
            status=row[7],
        )

    def _persist_entry(self, entry: KeyringEntry) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                """
                INSERT INTO keyring (
                    key_id, data_class, wrapped_dek, wrapping_key_id, algorithm, created_at, rotated_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.key_id,
                    entry.data_class.value,
                    entry.wrapped_dek,
                    entry.wrapping_key_id,
                    entry.algorithm,
                    entry.created_at.isoformat(),
                    entry.rotated_at.isoformat() if entry.rotated_at else None,
                    entry.status,
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def _update_entry_status(self, key_id: str, status: str, *, rotated_at: datetime | None) -> None:
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "UPDATE keyring SET status = ?, rotated_at = ? WHERE key_id = ?",
                (status, rotated_at.isoformat() if rotated_at else None, key_id),
            )
            connection.commit()
        finally:
            connection.close()

    def _require_scope(self, session: UnlockSession, scope: str) -> None:
        if session.is_expired():
            raise VaultStoreError("unlock session expired")
        if not session.allows(scope) and not session.allows("vault:key"):
            raise VaultStoreError(f"unlock session missing scope: {scope}")


@dataclass
class AesGcmCryptoProvider(CryptoProvider):
    """Authenticated encryption provider backed by AES-256-GCM."""

    key_manager: SQLiteKeyringKeyManager

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
        nonce = os.urandom(12)
        ciphertext = AESGCM(key.material).encrypt(nonce, plaintext, _canonical_aad(aad))
        return EncryptedRecord(
            record_id=record_id,
            data_class=data_class,
            key_id=key.key_id,
            nonce=nonce,
            ciphertext=ciphertext,
            aad=dict(aad),
            created_at=datetime.now(UTC),
            algorithm="AES-256-GCM",
        )

    def decrypt_record(
        self,
        record: EncryptedRecord,
        *,
        session: UnlockSession,
    ) -> bytes:
        entry = self.key_manager.load_entry_for_key_id(record.key_id)
        if entry is None:
            raise VaultStoreError("missing matching keyring entry for encrypted record")
        key = self.key_manager.unwrap_dek(entry, session=session)
        try:
            return AESGCM(key.material).decrypt(record.nonce, record.ciphertext, _canonical_aad(record.aad))
        except Exception as exc:  # pragma: no cover - cryptography error type is backend-specific
            raise VaultStoreError("failed to decrypt encrypted record") from exc


def build_sqlite_development_vault_runtime(
    *,
    path: Path,
    passphrase: str,
    profile_id: str = "default",
) -> VaultRuntime:
    """Build an explicit lower-assurance SQLite Local Vault runtime."""
    keychain = PassphraseKeychainProvider(passphrase=passphrase)
    session_manager = InMemoryUnlockSessionManager(keychain)
    key_manager = SQLiteKeyringKeyManager(path=path, keychain=keychain)
    crypto = AesGcmCryptoProvider(key_manager=key_manager)
    vault = SQLiteVaultStore(path=path, crypto=crypto, store_mode=VaultStoreMode.DEVELOPMENT)
    vault.initialize()
    repositories = build_vault_repository_bundle(vault, profile_id=profile_id)
    return VaultRuntime(
        mode=VaultStoreMode.DEVELOPMENT,
        profile_id=profile_id,
        keychain=keychain,
        session_manager=session_manager,
        vault=vault,
        repositories=repositories,
    )
