"""Resident daemon implementation preflight CLI helper."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from sayane.app import build_implementation_gate_preflight_report


def build_preflight_payload() -> dict[str, object]:
    """Build schema-only implementation gate preflight payload."""
    return build_implementation_gate_preflight_report().public_metadata()


def register_daemon_preflight_command(app_group: typer.Typer) -> None:
    """Register resident daemon implementation preflight preview command."""

    @app_group.command("daemon-preflight")
    def daemon_preflight(
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show resident daemon implementation gate preflight without side effects."""
        payload = build_preflight_payload()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"target_scope: {payload['target_scope']}")
        typer.echo(f"status: {payload['status']}")
        typer.echo(f"items: {len(payload['items'])}")
        typer.echo(f"mutates_filesystem: {payload['mutates_filesystem']}")
        typer.echo(f"probes_process: {payload['probes_process']}")
        typer.echo(f"controls_process: {payload['controls_process']}")
        typer.echo(f"exposes_ipc: {payload['exposes_ipc']}")
        typer.echo(f"integrates_os_service: {payload['integrates_os_service']}")
