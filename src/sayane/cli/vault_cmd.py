"""Built-in Local Vault diagnostic CLI commands."""

from __future__ import annotations

import json
import os
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
        development_mode: Annotated[
            bool,
            typer.Option("--development", help="Open explicit lower-assurance development runtime."),
        ] = False,
        test_mode: Annotated[
            bool,
            typer.Option("--test", help="Open explicit test-only runtime."),
        ] = False,
        sqlite_path: Annotated[
            Path | None,
            typer.Option("--sqlite", help="Open explicit SQLite runtime at path."),
        ] = None,
        passphrase_env: Annotated[
            str | None,
            typer.Option("--passphrase-env", help="Environment variable holding development vault passphrase."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Show Local Vault runtime status without exposing plaintext records."""
        if development_mode and test_mode:
            typer.echo("--development and --test are mutually exclusive")
            raise typer.Exit(2)
        if sqlite_path is not None and not (test_mode or development_mode):
            typer.echo("--sqlite requires --test or --development")
            raise typer.Exit(2)
        if passphrase_env is not None and not development_mode:
            typer.echo("--passphrase-env requires --development")
            raise typer.Exit(2)
        mode = "test" if test_mode else "development" if development_mode else "production"
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
                if test_mode:
                    runtime = build_sqlite_test_vault_runtime(path=sqlite_path, profile_id=profile_id)
                else:
                    runtime = open_vault_runtime(
                        mode="development",
                        profile_id=profile_id,
                        sqlite_path=sqlite_path,
                        passphrase=_read_passphrase(passphrase_env),
                    )
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
                    "supports_scoped_unlock_sessions": True,
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
            if development_mode:
                payload["lower_assurance"] = True
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
            if development_mode:
                typer.echo("  Warning: explicit passphrase runtime; lower assurance than OS-backed keychain")
        else:
            typer.echo(f"  Reason: {payload['reason']}")
            typer.echo("  Production Local Vault backend is intentionally fail-closed until implemented.")

    @vault_app.command("session")
    def vault_session(
        level: Annotated[
            UnlockLevel,
            typer.Option("--level", help="normal | sensitive | deep_private"),
        ] = UnlockLevel.SENSITIVE,
        purpose: Annotated[str, typer.Option("--purpose", help="Unlock purpose label.")] = "vault-session",
        development_mode: Annotated[
            bool,
            typer.Option("--development", help="Open explicit lower-assurance development runtime."),
        ] = False,
        test_mode: Annotated[
            bool,
            typer.Option("--test", help="Open explicit test-only runtime."),
        ] = False,
        sqlite_path: Annotated[
            Path | None,
            typer.Option("--sqlite", help="Open explicit SQLite runtime at path."),
        ] = None,
        passphrase_env: Annotated[
            str | None,
            typer.Option("--passphrase-env", help="Environment variable holding development vault passphrase."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Open one scoped unlock session and show non-secret metadata."""
        if development_mode and test_mode:
            typer.echo("--development and --test are mutually exclusive")
            raise typer.Exit(2)
        if sqlite_path is not None and not (test_mode or development_mode):
            typer.echo("--sqlite requires --test or --development")
            raise typer.Exit(2)
        if passphrase_env is not None and not development_mode:
            typer.echo("--passphrase-env requires --development")
            raise typer.Exit(2)

        if test_mode and sqlite_path is not None:
            runtime = build_sqlite_test_vault_runtime(path=sqlite_path, profile_id="default")
        elif test_mode:
            runtime = open_vault_runtime(mode="test", profile_id="default")
        elif development_mode:
            runtime = open_vault_runtime(
                mode="development",
                profile_id="default",
                sqlite_path=sqlite_path,
                passphrase=_read_passphrase(passphrase_env),
            )
        else:
            raise typer.BadParameter("session requires --test or --development")

        opener = getattr(runtime.session_manager, "open_policy_session", None)
        if opener is None:
            raise typer.BadParameter("runtime does not support policy-based sessions")
        session = opener(purpose, level)
        payload = {
            "kind": "local_vault_unlock_session",
            "runtime_mode": runtime.mode.value,
            "level": level.value,
            "purpose": session.purpose,
            "session_id": session.session_id,
            "assurance": session.assurance.value,
            "scopes": list(session.scopes),
            "unlocked_at": session.unlocked_at.isoformat(),
            "idle_expires_at": session.idle_expires_at.isoformat() if session.idle_expires_at else None,
            "expires_at": session.expires_at.isoformat(),
            "process_local": True,
            "reusable_across_processes": False,
        }
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"Session: {payload['session_id']}")
        typer.echo(f"  Level: {payload['level']}")
        typer.echo(f"  Assurance: {payload['assurance']}")
        typer.echo(f"  Expires: {payload['expires_at']}")
        typer.echo(f"  Idle expires: {payload['idle_expires_at']}")
        typer.echo("  Process local: true")

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


def _read_passphrase(passphrase_env: str | None) -> str:
    if not passphrase_env:
        raise VaultStoreError("development Local Vault backend requires --passphrase-env")
    value = os.environ.get(passphrase_env)
    if not value:
        raise VaultStoreError(
            f"development Local Vault backend requires non-empty environment variable: {passphrase_env}"
        )
    return value


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
