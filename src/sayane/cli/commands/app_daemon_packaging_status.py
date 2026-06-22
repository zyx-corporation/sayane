"""Resident daemon packaging-status CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_packaging_status
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_packaging_status_command(app_group: typer.Typer) -> None:
    """Register the resident daemon packaging-status command."""

    @app_group.command("daemon-packaging-status")
    def daemon_packaging_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the current operator-facing packaging and supervision boundary."""
        payload = build_daemon_packaging_status(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"packaging_model: {payload['packaging_model']}")
        typer.echo(f"supervision_model: {payload['supervision_model']}")
        typer.echo(f"service_integration_status: {payload['service_integration']['status']}")
