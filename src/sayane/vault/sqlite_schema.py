"""SQLite Local Vault schema contract.

This module defines the schema contract for the future production SQLite-backed
Local Vault. It intentionally does not open a database or implement persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


SCHEMA_VERSION = "local_vault.sqlite.v1"


class VaultTable(str, Enum):
    """SQLite tables required for encrypted Local Vault persistence."""

    KEYRING = "keyring"
    ENCRYPTED_RECORDS = "encrypted_records"
    AUDIT_METADATA = "audit_metadata"


KEYRING_COLUMNS: tuple[str, ...] = (
    "key_id",
    "data_class",
    "wrapped_dek",
    "wrapping_key_id",
    "algorithm",
    "created_at",
    "rotated_at",
    "status",
)

ENCRYPTED_RECORD_COLUMNS: tuple[str, ...] = (
    "record_id",
    "data_class",
    "key_id",
    "nonce",
    "ciphertext",
    "aad_json",
    "created_at",
    "updated_at",
)

AUDIT_METADATA_COLUMNS: tuple[str, ...] = (
    "event_id",
    "event_type",
    "record_id",
    "data_class",
    "metadata_json",
    "created_at",
)

FORBIDDEN_PRODUCTION_COLUMNS: tuple[str, ...] = (
    "plaintext",
    "plain_text",
    "raw_content",
    "master_key",
    "unwrapped_dek",
    "private_key",
)


@dataclass(frozen=True)
class TableContract:
    """Table name and required columns."""

    table: VaultTable
    columns: tuple[str, ...]


def required_table_contracts() -> tuple[TableContract, ...]:
    """Return required Local Vault SQLite table contracts."""
    return (
        TableContract(VaultTable.KEYRING, KEYRING_COLUMNS),
        TableContract(VaultTable.ENCRYPTED_RECORDS, ENCRYPTED_RECORD_COLUMNS),
        TableContract(VaultTable.AUDIT_METADATA, AUDIT_METADATA_COLUMNS),
    )


def validate_sqlite_vault_schema(
    tables: dict[str, tuple[str, ...]],
) -> list[str]:
    """Validate a SQLite schema description against the Local Vault contract."""
    errors: list[str] = []
    for contract in required_table_contracts():
        table_name = contract.table.value
        columns = tables.get(table_name)
        if columns is None:
            errors.append(f"missing table: {table_name}")
            continue
        missing = [col for col in contract.columns if col not in columns]
        if missing:
            errors.append(f"{table_name}: missing columns: {', '.join(missing)}")
        forbidden = [col for col in columns if col in FORBIDDEN_PRODUCTION_COLUMNS]
        if forbidden:
            errors.append(f"{table_name}: forbidden columns: {', '.join(forbidden)}")
    return errors


def create_table_statements() -> tuple[str, ...]:
    """Return reference CREATE TABLE statements for production implementation."""
    return (
        """
        CREATE TABLE IF NOT EXISTS keyring (
            key_id TEXT PRIMARY KEY,
            data_class TEXT NOT NULL,
            wrapped_dek BLOB NOT NULL,
            wrapping_key_id TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            created_at TEXT NOT NULL,
            rotated_at TEXT,
            status TEXT NOT NULL
        )
        """.strip(),
        """
        CREATE TABLE IF NOT EXISTS encrypted_records (
            record_id TEXT NOT NULL,
            data_class TEXT NOT NULL,
            key_id TEXT NOT NULL,
            nonce BLOB NOT NULL,
            ciphertext BLOB NOT NULL,
            aad_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            PRIMARY KEY (data_class, record_id),
            FOREIGN KEY (key_id) REFERENCES keyring(key_id)
        )
        """.strip(),
        """
        CREATE TABLE IF NOT EXISTS audit_metadata (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            record_id TEXT,
            data_class TEXT,
            metadata_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """.strip(),
    )
