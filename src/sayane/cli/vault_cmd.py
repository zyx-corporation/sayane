"""Built-in Local Vault diagnostic CLI commands."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.vault.contracts import VaultStoreError
from sayane.vault.factory import open_vault_runtime
from sayane.vault.sqlite_runtime import build_sqlite_test_vault_runtime
from sayane.vault.sqlite_schema import (
    FORBIDDEN_PRODUCTION_COLUMNS,
    SCHEMA_VERSION,
    create_table_statements,
    inspect_sqlite_tables,
    required_table_contracts,
    validate_sqlite_vault_schema,
)
from sayane.vault.unlock_policy import UnlockLevel, default_unlock_policy


def register_vault_cli(app: typer.Typer) -> None:
    """Register built-in `sayane vault ...` diagnostics."""
    vault_app = typer.Typer(help="Inspect Local Vault runtime status.", no_args_is_help=True)

    @vault_app.command("status")
    def vault_status(
        profile_id: Annotated[str, typer.Option("--profile-id", help="Profile id.")] = "default",
        test_mode: Annotated[
            bool,
            typer.Option("--test", help="Open explicit test-only runtime."),
        ] = False,
        sqlite_path: Annotated[
            Path | None,
            typer.Option("--sqlite", help="Open explicit test-only SQLite runtime at path."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Show Local Vault runtime status without exposing plaintext records."""
        if sqlite_path is not None and not test_mode:
            raise typer.BadParameter("--sqlite requires --test")
        mode = "test" if test_mode else "production"
        payload: dict[str, object] = {
            "profile_id": profile_id,
            "requested_mode": mode,
            "status": "unknown",
            "production_ready": False,
            "test_only": test_mode,
            "sqlite_backed": sqlite_path is not None,
        }
        try:
            if sqlite_path is not None:
                runtime = build_sqlite_test_vault_runtime(path=sqlite_path, profile_id=profile_id)
            else:
                runtime = open_vault_runtime(mode=mode, profile_id=profile_id)  # type: ignore[arg-type]
            caps = runtime.keychain.capabilities()
            payload.update(
                {
                    "status": "available",
                    "runtime_mode": runtime.mode.value,
                    "vault_mode": runtime.vault.mode().value,
                    "keychain_platform": caps.platform_name,
                    "keychain_assurance": caps.assurance.value,
                    "supports_biometric_unlock": caps.supports_biometric_unlock,
                    "supports_os_password_unlock": caps.supports_os_password_unlock,
                    "repositories": [
                        "candidate",
                        "review_decision",
                        "lineage",
                    ],
                },
            )
            if sqlite_path is not None:
                payload["sqlite_path"] = str(sqlite_path)
                payload["sqlite_schema_errors"] = validate_sqlite_vault_schema(
                    inspect_sqlite_tables(sqlite_path),
                )
        except VaultStoreError as exc:
            payload.update(
                {
                    "status": "unavailable",
                    "reason": str(exc),
                    "runtime_mode": mode,
                },
            )

        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        typer.echo(f"Local Vault: {payload['status']}")
        typer.echo(f"  Profile: {profile_id}")
        typer.echo(f"  Requested mode: {mode}")
        if payload["status"] == "available":
            typer.echo(f"  Runtime mode: {payload['runtime_mode']}")
            typer.echo(f"  Vault mode: {payload['vault_mode']}")
            typer.echo(f"  Keychain: {payload['keychain_platform']} ({payload['keychain_assurance']})")
            typer.echo("  Repositories: candidate, review_decision, lineage")
            if sqlite_path is not None:
                typer.echo(f"  SQLite: {sqlite_path}")
            if test_mode:
                typer.echo("  Warning: test-only runtime; not production cryptographic assurance")
        else:
            typer.echo(f"  Reason: {payload['reason']}")
            typer.echo("  Production Local Vault backend is intentionally fail-closed until implemented.")

    @vault_app.command("policy")
    def vault_policy(
        level: Annotated[
            str | None,
            typer.Option("--level", help="normal | sensitive | deep_private"),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Show Local Vault unlock policy presets without opening the vault."""
        levels = [UnlockLevel(level)] if level else list(UnlockLevel)
        policies = [_policy_payload(item) for item in levels]
        payload: object = policies[0] if level else {"policies": policies}

        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        for policy in policies:
            typer.echo(f"Unlock policy: {policy['level']}")
            typer.echo(f"  Idle timeout: {policy['idle_timeout_seconds']}s")
            typer.echo(f"  Absolute timeout: {policy['absolute_timeout_seconds']}s")
            typer.echo(f"  Explicit unlock: {policy['requires_explicit_unlock']}")
            typer.echo("  Scopes:")
            for scope in policy["scopes"]:
                typer.echo(f"    - {scope}")

    @vault_app.command("schema")
    def vault_schema(
        ddl: Annotated[
            bool,
            typer.Option("--ddl", help="Show reference CREATE TABLE statements."),
        ] = False,
        database: Annotated[
            Path | None,
            typer.Option("--database", help="Validate an existing SQLite database schema."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Show or validate SQLite Local Vault schema contract."""
        payload = _schema_payload(include_ddl=ddl)
        if database is not None:
            tables = inspect_sqlite_tables(database)
            errors = validate_sqlite_vault_schema(tables)
            payload.update(
                {
                    "database": str(database),
                    "validation_status": "pass" if not errors else "fail",
                    "validation_errors": errors,
                    "inspected_tables": [
                        {"name": name, "columns": list(columns)} for name, columns in tables.items()
                    ],
                },
            )

        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            if payload.get("validation_status") == "fail":
                raise typer.Exit(1)
            return

        typer.echo(f"SQLite Local Vault schema: {payload['schema_version']}")
        typer.echo("  Required tables:")
        for table in payload["tables"]:
            typer.echo(f"    - {table['name']}: {', '.join(table['columns'])}")
        typer.echo("  Forbidden production columns:")
        for column in payload["forbidden_production_columns"]:
            typer.echo(f"    - {column}")
        if ddl:
            typer.echo("  Reference DDL:")
            for statement in payload["create_table_statements"]:
                typer.echo(statement)
        if database is not None:
            typer.echo(f"  Database: {database}")
            typer.echo(f"  Validation: {payload['validation_status']}")
            for error in payload.get("validation_errors", []):
                typer.echo(f"    - {error}")
            if payload.get("validation_status") == "fail":
                raise typer.Exit(1)

    app.add_typer(vault_app, name="vault")


def _policy_payload(level: UnlockLevel) -> dict[str, object]:
    policy = default_unlock_policy(level)
    return {
        "level": policy.level.value,
        "idle_timeout_seconds": policy.idle_timeout_seconds,
        "absolute_timeout_seconds": policy.absolute_timeout_seconds,
        "requires_explicit_unlock": policy.requires_explicit_unlock,
        "scopes": list(policy.default_scopes),
    }


def _schema_payload(*, include_ddl: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": SCHEMA_VERSION,
        "tables": [
            {
                "name": contract.name,
                "columns": list(contract.required_columns),
            }
            for contract in required_table_contracts()
        ],
        "forbidden_production_columns": list(FORBIDDEN_PRODUCTION_COLUMNS),
    }
    if include_ddl:
        payload["create_table_statements"] = list(create_table_statements())
    return payload
