"""Resident daemon packaging-status CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_packaging_status
from sayane.bridge.config import BridgeConfig
from sayane.cli.commands._text_sections import echo_list_section, echo_object_section


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
        typer.echo(f"phase_status: {payload['phase_status']}")
        typer.echo(f"current_entrypoint: {payload['current_entrypoint']['command_text']}")
        typer.echo(f"service_integration_status: {payload['service_integration']['status']}")
        typer.echo(
            "service_integration_targets: "
            + ", ".join(payload["service_integration"].get("supported_targets", []) or ["—"])
        )
        typer.echo(f"background_supervision_status: {payload['background_supervision']['status']}")
        typer.echo(f"local_only: {payload['operator_commitments']['local_only']}")
        echo_object_section(
            "candidate_models",
            payload["packaging_decision"].get("candidate_models", []),
            lambda item: f"{item.get('model')}: {item.get('status')}",
        )
        echo_list_section(
            "decision_guardrails",
            payload["packaging_decision"].get("decision_guardrails", []),
        )
        echo_list_section(
            "local_daemon_commands",
            payload["local_daemon_control"].get("commands", []),
        )
        echo_list_section("next_phase_topics", payload.get("next_phase_topics", []))
