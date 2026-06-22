"""Resident daemon supervision-status CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_supervision_status
from sayane.bridge.config import BridgeConfig
from sayane.cli.commands._text_sections import echo_list_section, echo_object_section


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_supervision_status_command(app_group: typer.Typer) -> None:
    """Register the resident daemon supervision-status command."""

    @app_group.command("daemon-supervision-status")
    def daemon_supervision_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the current resident daemon supervision UX status."""
        payload = build_daemon_supervision_status(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"supervision_mode: {payload['supervision_mode']}")
        typer.echo(f"phase_status: {payload['phase_status']}")
        typer.echo(f"passive_visibility_status: {payload['passive_visibility']['status']}")
        typer.echo(f"active_supervision_status: {payload['active_supervision']['status']}")
        typer.echo(f"background_surface_status: {payload['background_surfaces']['status']}")
        echo_list_section(
            "passive_visibility_surfaces",
            payload["passive_visibility"].get("surfaces", []),
        )
        echo_list_section(
            "active_supervision_actions",
            payload["active_supervision"].get("allowed_actions", []),
        )
        echo_list_section(
            "deferred_background_topics",
            payload["background_surfaces"].get("deferred_topics", []),
        )
        echo_object_section(
            "candidate_background_surfaces",
            payload["background_surfaces"].get("candidate_surfaces", []),
            lambda item: f"{item.get('surface')}: {item.get('status')}",
        )
        echo_list_section(
            "decision_guardrails",
            payload["background_surfaces"].get("decision_guardrails", []),
        )
        echo_list_section("recovery_entrypoints", payload.get("recovery_entrypoints", []))
