"""Resident daemon LaunchAgent CLI helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    ResidentDaemonLaunchAgentApplyError,
    apply_launchagent_plan,
    build_launchagent_plan,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_launchagent_commands(app_group: typer.Typer) -> None:
    """Register macOS LaunchAgent preview/apply commands."""

    @app_group.command("daemon-launchagent-preview")
    def daemon_launchagent_preview(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        payload = build_launchagent_plan(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"label: {payload['label']}")
        typer.echo(f"plist_path: {payload['plist_path']}")

    @app_group.command("daemon-launchagent-apply")
    def daemon_launchagent_apply(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_id: Annotated[str | None, typer.Option("--operation-id")] = None,
        confirm_operation_id: Annotated[str | None, typer.Option("--confirm-operation-id")] = None,
        confirm_preview_hash: Annotated[str | None, typer.Option("--confirm-preview-hash")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        plan = build_launchagent_plan(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
            operation_id=operation_id or confirm_operation_id,
        )
        try:
            payload = apply_launchagent_plan(
                plan,
                confirm_operation_id=confirm_operation_id,
                confirm_preview_hash=confirm_preview_hash,
            )
        except ResidentDaemonLaunchAgentApplyError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"plist_path: {payload['plist_path']}")
        typer.echo(f"result: {payload['result']}")
