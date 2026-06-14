"""Built-in Local Vault diagnostic CLI commands."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from sayane.vault.contracts import VaultStoreError
from sayane.vault.factory import open_vault_runtime


def register_vault_cli(app: typer.Typer) -> None:
    """Register built-in `sayane vault ...` diagnostics."""
    vault_app = typer.Typer(help="Inspect Local Vault runtime status.", no_args_is_help=True)

    @vault_app.command("status")
    def vault_status(
        profile_id: Annotated[str, typer.Option("--profile-id", help="Profile id.")] = "default",
        test_mode: Annotated[bool, typer.Option("--test", help="Open explicit test-only runtime.")] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON.")] = False,
    ) -> None:
        """Show Local Vault runtime status without exposing plaintext records."""
        mode = "test" if test_mode else "production"
        payload: dict[str, object] = {
            "profile_id": profile_id,
            "requested_mode": mode,
            "status": "unknown",
            "production_ready": False,
            "test_only": test_mode,
        }
        try:
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
            if test_mode:
                typer.echo("  Warning: test-only runtime; not production cryptographic assurance")
        else:
            typer.echo(f"  Reason: {payload['reason']}")
            typer.echo("  Production Local Vault backend is intentionally fail-closed until implemented.")

    app.add_typer(vault_app, name="vault")
