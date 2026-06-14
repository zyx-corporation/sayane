"""Tests for Local Vault diagnostic CLI."""

from __future__ import annotations

import json
import sqlite3

from typer.testing import CliRunner

from sayane.cli.app import build_app
from sayane.vault.sqlite_schema import create_table_statements


def test_vault_status_default_reports_no_production_backend() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "unavailable"
    assert payload["requested_mode"] == "production"
    assert payload["production_ready"] is False


def test_vault_status_test_mode_requires_explicit_flag() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "status", "--test", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "available"
    assert payload["requested_mode"] == "test"
    assert payload["runtime_mode"] == "test"
    assert payload["vault_mode"] == "test"
    assert payload["keychain_assurance"] == "test_only"
    assert payload["test_only"] is True
    assert payload["production_ready"] is False
    assert payload["repositories"] == ["candidate", "review_decision", "lineage"]


def test_vault_status_sqlite_requires_test_flag(tmp_path) -> None:
    result = CliRunner().invoke(
        build_app(),
        ["vault", "status", "--sqlite", str(tmp_path / "vault.sqlite"), "--json"],
    )

    assert result.exit_code != 0
    assert "--sqlite requires --test" in result.output


def test_vault_status_sqlite_test_mode_is_explicit(tmp_path) -> None:
    db_path = tmp_path / "vault.sqlite"
    result = CliRunner().invoke(
        build_app(),
        ["vault", "status", "--test", "--sqlite", str(db_path), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "available"
    assert payload["requested_mode"] == "test"
    assert payload["test_only"] is True
    assert payload["sqlite_backed"] is True
    assert payload["sqlite_path"] == str(db_path)
    assert payload["sqlite_schema_errors"] == []
    assert payload["production_ready"] is False


def test_vault_policy_lists_all_presets() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "policy", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    levels = [item["level"] for item in payload["policies"]]
    assert levels == ["normal", "sensitive", "deep_private"]


def test_vault_policy_can_show_sensitive_preset() -> None:
    result = CliRunner().invoke(
        build_app(),
        ["vault", "policy", "--level", "sensitive", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["level"] == "sensitive"
    assert payload["idle_timeout_seconds"] == 5 * 60
    assert payload["absolute_timeout_seconds"] == 15 * 60
    assert "candidate:write" in payload["scopes"]
    assert "review_decision:write" in payload["scopes"]
    assert "lineage:write" in payload["scopes"]
    assert "deep_private:read" not in payload["scopes"]


def test_vault_schema_reports_required_tables_and_forbidden_columns() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "schema", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "local_vault.sqlite.v1"
    table_names = [table["name"] for table in payload["tables"]]
    assert table_names == ["keyring", "encrypted_records", "audit_metadata"]
    assert "wrapped_dek" in payload["tables"][0]["columns"]
    assert "ciphertext" in payload["tables"][1]["columns"]
    assert "aad_json" in payload["tables"][1]["columns"]
    assert "plaintext" in payload["forbidden_production_columns"]
    assert "master_key" in payload["forbidden_production_columns"]


def test_vault_schema_can_include_reference_ddl() -> None:
    result = CliRunner().invoke(build_app(), ["vault", "schema", "--ddl", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    ddl = "\n".join(payload["create_table_statements"]).lower()
    assert "create table if not exists keyring" in ddl
    assert "create table if not exists encrypted_records" in ddl
    assert "create table if not exists audit_metadata" in ddl
    assert "ciphertext" in ddl
    assert "master_key" not in ddl


def test_vault_schema_database_validation_passes_for_reference_schema(tmp_path) -> None:
    db_path = tmp_path / "vault.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        for statement in create_table_statements():
            connection.execute(statement)
        connection.commit()
    finally:
        connection.close()

    result = CliRunner().invoke(
        build_app(),
        ["vault", "schema", "--database", str(db_path), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["validation_status"] == "pass"
    assert payload["validation_errors"] == []


def test_vault_schema_database_validation_fails_for_plaintext_column(tmp_path) -> None:
    db_path = tmp_path / "bad-vault.sqlite"
    connection = sqlite3.connect(db_path)
    try:
        for statement in create_table_statements():
            connection.execute(statement)
        connection.execute("ALTER TABLE encrypted_records ADD COLUMN plaintext TEXT")
        connection.commit()
    finally:
        connection.close()

    result = CliRunner().invoke(
        build_app(),
        ["vault", "schema", "--database", str(db_path), "--json"],
    )

    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["validation_status"] == "fail"
    assert any("forbidden columns: plaintext" in error for error in payload["validation_errors"])
