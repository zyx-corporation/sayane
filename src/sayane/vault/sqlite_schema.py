"""SQLite Local Vault schema contract.

This module defines the schema contract for the future production SQLite-backed
Local Vault. It does not implement persistence, but it can inspect an existing
SQLite database schema without reading encrypted record content.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path


SCHEMA_VERSION = "local_vault.sqlite.v1"


class VaultTable(StrEnum):
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
    "profile_id",
    "data_class",
    "record_id",
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
    """Required and forbidden columns for one SQLite table."""

    name: str
    required_columns: tuple[str, ...]
    forbidden_columns: tuple[str, ...] = FORBIDDEN_PRODUCTION_COLUMNS


def required_table_contracts() -> tuple[TableContract, ...]:
    """Return the required SQLite vault table contracts."""
    return (
        TableContract(VaultTable.KEYRING.value, KEYRING_COLUMNS),
        TableContract(VaultTable.ENCRYPTED_RECORDS.value, ENCRYPTED_RECORD_COLUMNS),
        TableContract(VaultTable.AUDIT_METADATA.value, AUDIT_METADATA_COLUMNS),
    )


def validate_sqlite_vault_schema(tables: dict[str, set[str]]) -> list[str]:
    """Validate SQLite schema metadata without inspecting record rows."""
    errors: list[str] = []
    for contract in required_table_contracts():
        columns = tables.get(contract.name)
        if columns is None:
            errors.append(f"missing required table: {contract.name}")
            continue
        for column in contract.required_columns:
            if column not in columns:
                errors.append(f"missing required column: {contract.name}.{column}")
        for column in contract.forbidden_columns:
            if column in columns:
                errors.append(f"forbidden plaintext/key column: {contract.name}.{column}")
    return errors


def inspect_sqlite_tables(path: Path) -> dict[str, set[str]]:
    """Inspect SQLite table metadata only.

    This deliberately uses sqlite_master and PRAGMA table_info. It must not read
    record rows from encrypted_records.
    """
    connection = sqlite3.connect(path)
    try:
        table_rows = connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name"
        ).fetchall()
        tables: dict[str, set[str]] = {}
        for (table_name,) in table_rows:
            column_rows = connection.execute(
                f"PRAGMA table_info({quote_sqlite_identifier(table_name)})"
            ).fetchall()
            tables[table_name] = {row[1] for row in column_rows}
        return tables
    finally:
        connection.close()


def quote_sqlite_identifier(identifier: str) -> str:
    """Quote a SQLite identifier for PRAGMA metadata inspection."""
    return '"' + identifier.replace('"', '""') + '"'


def create_table_statements() -> tuple[str, ...]:
    """Return reference CREATE TABLE statements for the schema contract."""
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
        """,
        """
        CREATE TABLE IF NOT EXISTS encrypted_records (
            record_id TEXT NOT NULL,
            data_class TEXT NOT NULL,
            key_id TEXT NOT NULL,
            nonce BLOB NOT NULL,
            ciphertext BLOB NOT NULL,
            aad_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (data_class, record_id)
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS audit_metadata (
            event_id TEXT PRIMARY KEY,
            event_type TEXT NOT NULL,
            profile_id TEXT,
            data_class TEXT,
            record_id TEXT,
            created_at TEXT NOT NULL
        )
        """,
    )
