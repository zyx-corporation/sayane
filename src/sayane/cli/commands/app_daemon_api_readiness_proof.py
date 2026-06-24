"""Resident daemon API-readiness proof CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_api_readiness_proof_command(app_group: typer.Typer) -> None:
    """Register read-only API-readiness proof preview command."""

    @app_group.command("daemon-api-readiness-proof")
    def daemon_api_readiness_proof(
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
                help="Operator-visible API-readiness target such as bridge_health or diagnostics.",
            ),
        ] = "bridge_health",
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Report conservative daemon API-readiness proof observations."""
        from sayane.app import build_api_readiness_proof

        payload = build_api_readiness_proof(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
            operation_class=operation_class,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"operation_class: {payload['operation_class']}")
        typer.echo(f"api_readiness_status: {payload['api_readiness_status']}")
        typer.echo(f"evidence_ceiling: {payload['evidence_ceiling']}")
        typer.echo(f"manual_review_required: {payload['manual_review_required']}")
        typer.echo(f"proves_api_readiness: {payload['proves_api_readiness']}")
