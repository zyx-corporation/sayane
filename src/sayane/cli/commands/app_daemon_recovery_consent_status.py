"""Resident daemon recovery-consent-status CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_recovery_consent_status
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_recovery_consent_status_command(app_group: typer.Typer) -> None:
    """Register the resident daemon recovery-consent-status command."""

    @app_group.command("daemon-recovery-consent-status")
    def daemon_recovery_consent_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the current resident daemon recovery and consent boundary."""
        payload = build_daemon_recovery_consent_status(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"consent_model: {payload['consent_model']}")
        typer.echo(f"recovery_model: {payload['recovery_model']}")
