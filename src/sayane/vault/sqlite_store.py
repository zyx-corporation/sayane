"""SQLite-backed Local Vault store.

This store persists encrypted records produced by a CryptoProvider. It does not
perform plaintext storage and does not implement platform keychain integration
by itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import sqlite3

from sayane.vault.contracts import (
    CryptoProvider,
    DataClass,
    EncryptedRecord,
    UnlockSession,
    VaultStore,
    VaultStoreError,
    VaultStoreMode,
)
from sayane.vault.sqlite_schema import create_table_statements


@dataclass
class SQLiteVaultStore(VaultStore):
    """SQLite persistence adapter for encrypted Local Vault records."""

    path: Path
    crypto: CryptoProvider
    store_mode: VaultStoreMode = VaultStoreMode.DEVELOPMENT

    def mode(self) -> VaultStoreMode:
        return self.store_mode

    def is_plaintext_default(self) -> bool:
        return False

    def initialize(self) -> None:
        """Create schema tables if missing."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        try:
            for statement in create_table_statements():
                connection.execute(statement)
            connection.commit()
        finally:
            connection.close()

    def put(
        self,
        data_class: DataClass,
        record_id: str,
        plaintext: bytes,
        aad: dict[str, str],
        session: UnlockSession,
    ) -> None:
        session.require(f"{data_class.value}:write")
        encrypted = self.crypto.encrypt_record(data_class, record_id, plaintext, aad, session)
        self._upsert_record(encrypted)

    def get(
        self,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> bytes:
        session.require(f"{data_class.value}:read")
        encrypted = self._load_record(data_class, record_id)
        if encrypted is None:
            raise VaultStoreError(f"record not found: {data_class.value}/{record_id}")
        return self.crypto.decrypt_record(encrypted, session)

    def delete(
        self,
        data_class: DataClass,
        record_id: str,
        session: UnlockSession,
    ) -> None:
        session.require(f"{data_class.value}:delete")
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                "DELETE FROM encrypted_records WHERE data_class = ? AND record_id = ?",
                (data_class.value, record_id),
            )
            connection.commit()
        finally:
            connection.close()

    def list_record_ids(
        self,
        data_class: DataClass,
        session: UnlockSession,
    ) -> list[str]:
        session.require(f"{data_class.value}:read")
        connection = sqlite3.connect(self.path)
        try:
            rows = connection.execute(
                "SELECT record_id FROM encrypted_records WHERE data_class = ? ORDER BY created_at, record_id",
                (data_class.value,),
            ).fetchall()
            return [row[0] for row in rows]
        finally:
            connection.close()

    def _upsert_record(self, encrypted: EncryptedRecord) -> None:
        self.initialize()
        connection = sqlite3.connect(self.path)
        try:
            connection.execute(
                """
                INSERT INTO encrypted_records (
                    record_id,
                    data_class,
                    key_id,
                    nonce,
                    ciphertext,
                    aad_json,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(data_class, record_id) DO UPDATE SET
                    key_id = excluded.key_id,
                    nonce = excluded.nonce,
                    ciphertext = excluded.ciphertext,
                    aad_json = excluded.aad_json,
                    updated_at = excluded.updated_at
                """,
                (
                    encrypted.record_id,
                    encrypted.data_class.value,
                    encrypted.key_id,
                    encrypted.nonce,
                    encrypted.ciphertext,
                    json.dumps(encrypted.aad, ensure_ascii=False, sort_keys=True),
                    encrypted.created_at.isoformat(),
                    encrypted.created_at.isoformat(),
                ),
            )
            connection.commit()
        finally:
            connection.close()

    def _load_record(self, data_class: DataClass, record_id: str) -> EncryptedRecord | None:
        connection = sqlite3.connect(self.path)
        try:
            row = connection.execute(
                """
                SELECT record_id, data_class, key_id, nonce, ciphertext, aad_json, created_at
                FROM encrypted_records
                WHERE data_class = ? AND record_id = ?
                """,
                (data_class.value, record_id),
            ).fetchone()
            if row is None:
                return None
            from datetime import datetime

            return EncryptedRecord(
                record_id=row[0],
                data_class=DataClass(row[1]),
                key_id=row[2],
                nonce=row[3],
                ciphertext=row[4],
                aad=json.loads(row[5]),
                created_at=datetime.fromisoformat(row[6]),
            )
        finally:
            connection.close()
