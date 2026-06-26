"""Resident daemon service/control boundary CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_daemon_service_control_boundary
from sayane.bridge.config import BridgeConfig
from sayane.cli.commands._text_sections import echo_list_section, echo_object_section


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
        typer.echo(f"rollback_required: {payload['service_plane']['rollback_required']}")
        typer.echo(f"platform_policy_required: {payload['service_plane']['platform_policy_required']}")
        typer.echo(f"update_strategy: {payload['service_plane']['update_strategy']}")
        echo_list_section(
            "control_plane_allowed_commands",
            [item.get("command") for item in payload["control_plane"].get("allowed_commands", [])],
        )
        echo_list_section(
            "control_plane_recovery_policy",
            payload["control_plane"].get("recovery_policy", []),
        )
        echo_list_section(
            "service_plane_allowed_commands",
            [item.get("command") for item in payload["service_plane"].get("allowed_commands", [])],
        )
        echo_list_section(
            "service_plane_platform_targets",
            payload["service_plane"].get("platform_targets", []),
        )
        echo_list_section(
            "deferred_commands",
            payload["service_plane"].get("deferred_commands", []),
        )
        echo_object_section(
            "lifecycle_operations",
            payload["service_plane"].get("lifecycle_operations", []),
            lambda item: f"{item.get('operation')}: {item.get('status')} [{item.get('command')}]",
        )
        echo_list_section("allowed_reads", payload["app_ui_policy"].get("allowed_reads", []))
        echo_list_section(
            "allowed_control_exposure",
            payload["app_ui_policy"].get("allowed_control_exposure", []),
        )
        echo_list_section(
            "forbidden_control_exposure",
            payload["app_ui_policy"].get("forbidden_control_exposure", []),
        )
