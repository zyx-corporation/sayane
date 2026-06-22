"""Resident daemon proof diagnostics CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    build_api_readiness_proof,
    build_identity_proof,
    build_readiness_proof,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_proof_diagnostics_command(app_group: typer.Typer) -> None:
    """Register read-only aggregated daemon proof diagnostics command."""

    @app_group.command("daemon-proof-diagnostics")
    def daemon_proof_diagnostics(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_class: Annotated[
            str,
            typer.Option(
                "--operation-class",
                help="Operator-visible readiness/API-readiness target such as bridge_health or diagnostics.",
            ),
        ] = "bridge_health",
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Report aggregated identity/readiness/API proof observations."""
        effective_runtime_root = runtime_root or _default_runtime_root()
        identity = build_identity_proof(
            effective_runtime_root,
            host=host,
            port=port,
        ).public_metadata()
        readiness = build_readiness_proof(
            effective_runtime_root,
            host=host,
            port=port,
            operation_class=operation_class,
        ).public_metadata()
        api = build_api_readiness_proof(
            effective_runtime_root,
            host=host,
            port=port,
            operation_class=operation_class,
        ).public_metadata()
        payload = {
            "kind": "resident_daemon_proof_diagnostics_preview",
            "preview_only": True,
            "runtime_root": str(effective_runtime_root),
            "operation_class": operation_class,
            "identity_proof": identity,
            "readiness_proof": readiness,
            "api_readiness_proof": api,
            "mutates_filesystem": False,
            "controls_process": False,
        }
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"operation_class: {payload['operation_class']}")
        typer.echo(f"identity_status: {identity['identity_status']}")
        typer.echo(f"readiness_status: {readiness['readiness_status']}")
        typer.echo(f"api_readiness_status: {api['api_readiness_status']}")
        typer.echo(f"preview_only: {payload['preview_only']}")
