"""Resident daemon identity-proof CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_identity_proof
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_identity_proof_command(app_group: typer.Typer) -> None:
    """Register read-only daemon identity-proof preview command."""

    @app_group.command("daemon-identity-proof")
    def daemon_identity_proof(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Report conservative daemon identity-proof observations."""
        payload = build_identity_proof(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"identity_status: {payload['identity_status']}")
        typer.echo(f"evidence_ceiling: {payload['evidence_ceiling']}")
        typer.echo(f"manual_review_required: {payload['manual_review_required']}")
        typer.echo(f"proves_process_identity: {payload['proves_process_identity']}")
