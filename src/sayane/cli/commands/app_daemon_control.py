"""Resident daemon process-control CLI helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    ResidentDaemonProcessControlError,
    build_daemon_status_report,
    restart_resident_daemon,
    start_resident_daemon,
    stop_resident_daemon,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def _emit_payload(payload: dict[str, object], *, json_out: bool) -> None:
    if json_out:
        typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
        return
    typer.echo(f"kind: {payload['kind']}")
    typer.echo(f"operation: {payload.get('operation', 'status')}")
    typer.echo(f"state: {payload.get('state', payload.get('state_after'))}")
    typer.echo(f"result: {payload.get('result', 'status')}")


def register_daemon_control_commands(app_group: typer.Typer) -> None:
    """Register minimal resident daemon process-control commands."""

    @app_group.command("daemon-start")
    def daemon_start(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        wait_seconds: Annotated[
            float,
            typer.Option("--wait-seconds", help="Seconds to wait for readiness."),
        ] = 5.0,
        include_event_record: Annotated[
            bool,
            typer.Option(
                "--include-event-record",
                help="Include a derived resident daemon event record in the payload.",
            ),
        ] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Start the local-only resident daemon subprocess."""
        try:
            payload = start_resident_daemon(
                runtime_root or _default_runtime_root(),
                host=host,
                port=port,
                wait_seconds=wait_seconds,
                include_event_record=include_event_record,
            )
        except ResidentDaemonProcessControlError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        _emit_payload(payload, json_out=json_out)

    @app_group.command("daemon-stop")
    def daemon_stop(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        wait_seconds: Annotated[
            float,
            typer.Option("--wait-seconds", help="Seconds to wait for shutdown."),
        ] = 5.0,
        include_event_record: Annotated[
            bool,
            typer.Option(
                "--include-event-record",
                help="Include a derived resident daemon event record in the payload.",
            ),
        ] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Stop the local-only resident daemon subprocess."""
        try:
            payload = stop_resident_daemon(
                runtime_root or _default_runtime_root(),
                host=host,
                port=port,
                wait_seconds=wait_seconds,
                include_event_record=include_event_record,
            )
        except ResidentDaemonProcessControlError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        _emit_payload(payload, json_out=json_out)

    @app_group.command("daemon-restart")
    def daemon_restart(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        wait_seconds: Annotated[
            float,
            typer.Option("--wait-seconds", help="Seconds to wait for restart."),
        ] = 5.0,
        include_event_record: Annotated[
            bool,
            typer.Option(
                "--include-event-record",
                help="Include a derived resident daemon event record in the payload.",
            ),
        ] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Restart the local-only resident daemon subprocess."""
        try:
            payload = restart_resident_daemon(
                runtime_root or _default_runtime_root(),
                host=host,
                port=port,
                wait_seconds=wait_seconds,
                include_event_record=include_event_record,
            )
        except ResidentDaemonProcessControlError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        _emit_payload(payload, json_out=json_out)

    @app_group.command("daemon-status")
    def daemon_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show actual local-only resident daemon status."""
        try:
            payload = build_daemon_status_report(
                runtime_root or _default_runtime_root(),
                host=host,
                port=port,
            ).public_metadata()
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        _emit_payload(payload, json_out=json_out)
