"""Plan-only resident daemon lifecycle CLI helpers."""

from __future__ import annotations

import json
import shlex
from typing import Annotated, Any

import typer

def _lifecycle(host: str, port: int) -> ResidentDaemonLifecycle:
    from sayane.app import ResidentDaemonLifecycle

    try:
        return ResidentDaemonLifecycle(host=host, port=port)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _base_plan(host: str, port: int) -> dict[str, Any]:
    from sayane.app import ResidentDaemonMode

    lifecycle = _lifecycle(host, port)
    bridge_command = ["sayane", "serve", "--host", host, "--port", str(port)]
    payload = lifecycle.public_metadata()
    payload.update(
        {
            "mode": ResidentDaemonMode.BRIDGE_DELEGATION.value,
            "plan_only": True,
            "current_serve_path": "delegate_to_sayane_serve",
            "bridge_command": bridge_command,
            "bridge_command_text": " ".join(shlex.quote(part) for part in bridge_command),
        },
    )
    return payload


def build_operation_plan(host: str, port: int, operation: str) -> dict[str, Any]:
    """Build a plan-only lifecycle operation payload."""
    from sayane.app import ResidentDaemonState

    lifecycle = _lifecycle(host, port)
    target_by_operation = {
        "start": ResidentDaemonState.STARTING,
        "stop": ResidentDaemonState.STOPPING,
        "restart": ResidentDaemonState.STARTING,
    }
    target = target_by_operation[operation]
    payload = _base_plan(host, port)
    payload.update(
        {
            "kind": "resident_daemon_operation_plan",
            "operation": operation,
            "target_state": target.value,
            "transition_allowed": lifecycle.can_transition_to(target),
            "would_start_daemon": False,
            "would_stop_daemon": False,
            "would_restart_daemon": False,
        },
    )
    payload["planned_sequence"] = (
        ["stop-if-running", "start"] if operation == "restart" else [operation]
    )
    return payload


def _emit_plan(payload: dict[str, Any], *, json_out: bool) -> None:
    if json_out:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo(f"operation: {payload['operation']}")
    typer.echo(f"target_state: {payload['target_state']}")
    typer.echo(f"plan_only: {payload['plan_only']}")


def register_daemon_plan_commands(app_group: typer.Typer) -> None:
    """Register plan-only resident daemon operation commands."""

    @app_group.command("daemon-start-plan")
    def daemon_start_plan(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show a daemon start operation plan without starting anything."""
        _emit_plan(build_operation_plan(host, port, "start"), json_out=json_out)

    @app_group.command("daemon-stop-plan")
    def daemon_stop_plan(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show a daemon stop operation plan without stopping anything."""
        _emit_plan(build_operation_plan(host, port, "stop"), json_out=json_out)

    @app_group.command("daemon-restart-plan")
    def daemon_restart_plan(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show a daemon restart operation plan without restarting anything."""
        _emit_plan(build_operation_plan(host, port, "restart"), json_out=json_out)
