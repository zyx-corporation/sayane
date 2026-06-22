"""Resident daemon service/control boundary CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_service_control_boundary
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_service_control_boundary_command(app_group: typer.Typer) -> None:
    """Register the resident daemon service/control boundary command."""

    @app_group.command("daemon-service-control-boundary")
    def daemon_service_control_boundary(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the current resident daemon service/control boundary."""
        payload = build_daemon_service_control_boundary(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"control_plane_status: {payload['control_plane']['status']}")
        typer.echo(f"service_plane_status: {payload['service_plane']['status']}")
