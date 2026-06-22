"""Resident daemon operator packaging/supervision phase status CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_operator_phase_status
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_operator_phase_status_command(app_group: typer.Typer) -> None:
    """Register the aggregated operator packaging/supervision phase status command."""

    @app_group.command("daemon-operator-phase-status")
    def daemon_operator_phase_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the aggregated post-app operator packaging/supervision phase status."""
        payload = build_daemon_operator_phase_status(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"phase: {payload['phase']}")
        typer.echo(f"phase_status: {payload['phase_status']}")
        typer.echo(f"phase_readiness: {payload['phase_readiness']}")
        operator_path = payload.get("current_supported_operator_path", {})
        typer.echo(f"startup_command: {operator_path.get('startup_command_text', '—')}")
        typer.echo(f"bootstrap_ui: {operator_path.get('bootstrap_ui', '—')}")
        typer.echo(f"local_only: {operator_path.get('local_only')}")
        blocking_reasons = payload.get("blocking_reasons", [])
        typer.echo(f"blocking_reasons: {', '.join(blocking_reasons) if blocking_reasons else '—'}")
        typer.echo(f"recommended_order: {', '.join(payload['recommended_implementation_order'])}")
        typer.echo("workstreams:")
        for item in payload.get("workstreams", []):
            detail = (
                item.get("current_state")
                or item.get("current_target")
                or item.get("background_status")
                or item.get("consent_model")
                or "—"
            )
            typer.echo(f"  - {item.get('name')}: {item.get('status')} ({detail})")
        typer.echo("read_surfaces:")
        for read_surface in payload.get("read_surfaces", []):
            typer.echo(f"  - {read_surface}")
        typer.echo("exit_criteria:")
        for item in payload.get("exit_criteria", []):
            typer.echo(f"  - {item}")
        typer.echo("not_in_scope:")
        for item in payload.get("not_in_scope", []):
            typer.echo(f"  - {item}")
