"""Tests for SQLite Local Vault schema contract."""

from __future__ import annotations

import sqlite3

from sayane.vault.sqlite_schema import (
    AUDIT_METADATA_COLUMNS,
    ENCRYPTED_RECORD_COLUMNS,
    KEYRING_COLUMNS,
    VaultTable,
    create_table_statements,
    inspect_sqlite_tables,
    quote_sqlite_identifier,
    required_table_contracts,
    validate_sqlite_vault_schema,
)


def test_required_table_contracts_cover_vault_tables() -> None:
    contracts = required_table_contracts()
    assert [contract.table for contract in contracts] == [
        VaultTable.KEYRING,
        VaultTable.ENCRYPTED_RECORDS,
        VaultTable.AUDIT_METADATA,
    ]


def test_sqlite_schema_validation_accepts_required_tables() -> None:
    errors = validate_sqlite_vault_schema(
        {
            "keyring": KEYRING_COLUMNS,
            "encrypted_records": ENCRYPTED_RECORD_COLUMNS,
            "audit_metadata": AUDIT_METADATA_COLUMNS,
        },
    )
    assert errors == []


def test_sqlite_schema_validation_rejects_missing_table() -> None:
    errors = validate_sqlite_vault_schema(
        {
            "keyring": KEYRING_COLUMNS,
            "encrypted_records": ENCRYPTED_RECORD_COLUMNS,
        },
    )
    assert "missing table: audit_metadata" in errors


def test_sqlite_schema_validation_rejects_missing_required_column() -> None:
    errors = validate_sqlite_vault_schema(
        {
            "keyring": tuple(col for col in KEYRING_COLUMNS if col != "wrapped_dek"),
            "encrypted_records": ENCRYPTED_RECORD_COLUMNS,
            "audit_metadata": AUDIT_METADATA_COLUMNS,
        },
    )
    assert any("keyring: missing columns: wrapped_dek" in error for error in errors)


def test_sqlite_schema_validation_rejects_plaintext_columns() -> None:
    errors = validate_sqlite_vault_schema(
        {
            "keyring": KEYRING_COLUMNS + ("master_key",),
            "encrypted_records": ENCRYPTED_RECORD_COLUMNS + ("plaintext",),
            "audit_metadata": AUDIT_METADATA_COLUMNS,
        },
    )
    assert any("keyring: forbidden columns: master_key" in error for error in errors)
    assert any("encrypted_records: forbidden columns: plaintext" in error for error in errors)


def test_create_table_statements_include_no_plaintext_columns() -> None:
    statements = create_table_statements()
    joined = "\n".join(statements).lower()

    assert "create table if not exists keyring" in joined
    assert "create table if not exists encrypted_records" in joined
    assert "create table if not exists audit_metadata" in joined
    assert "wrapped_dek" in joined
    assert "ciphertext" in joined
    assert "aad_json" in joined
    assert " plaintext" not in joined
    assert "master_key" not in joined


def test_quote_sqlite_identifier_escapes_double_quotes() -> None:
    assert quote_sqlite_identifier('a"b') == '"a""b"'


def test_inspect_sqlite_tables_reads_metadata_only(tmp_path) -> None:
    db_path = tmp_path / "vault.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        for statement in create_table_statements():
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()

    tables = inspect_sqlite_tables(db_path)

    assert tables["keyring"] == KEYRING_COLUMNS
    assert tables["encrypted_records"] == ENCRYPTED_RECORD_COLUMNS
    assert tables["audit_metadata"] == AUDIT_METADATA_COLUMNS
    assert validate_sqlite_vault_schema(tables) == []
