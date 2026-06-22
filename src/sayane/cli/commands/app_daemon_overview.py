"""Resident daemon overview CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_overview_preview, create_local_capability_token
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_overview_command(app_group: typer.Typer) -> None:
    """Register resident daemon overview preview command."""

    @app_group.command("daemon-overview")
    def daemon_overview(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show a future-UI-oriented resident daemon overview preview."""
        payload = build_daemon_overview_preview(
            runtime_root or _default_runtime_root(),
            capability=create_local_capability_token(["ui"]),
            host=host,
            port=port,
        )
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"runtime_root: {payload['runtime_root']}")
        typer.echo(f"state: {payload['status']['state']}")
        typer.echo(f"liveness: {payload['liveness']['status']}")
        typer.echo(f"readiness: {payload['readiness']['readiness_status']}")
        typer.echo(f"next_actions: {len(payload['next_actions'])}")
