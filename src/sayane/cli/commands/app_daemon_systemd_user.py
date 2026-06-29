"""Resident daemon Linux systemd --user CLI helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    ResidentDaemonSystemdUserApplyError,
    ResidentDaemonSystemdUserControlError,
    apply_systemd_user_plan,
    build_systemd_user_plan,
    build_systemd_user_status,
    run_systemd_user_command,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_systemd_user_commands(app_group: typer.Typer) -> None:
    """Register Linux systemd --user preview/apply commands."""

    @app_group.command("daemon-systemd-user-preview")
    def daemon_systemd_user_preview(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        payload = build_systemd_user_plan(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        ).public_metadata()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"unit_name: {payload['unit_name']}")
        typer.echo(f"unit_path: {payload['unit_path']}")

    @app_group.command("daemon-systemd-user-apply")
    def daemon_systemd_user_apply(
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
        plan = build_systemd_user_plan(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
            operation_id=operation_id or confirm_operation_id,
        )
        try:
            payload = apply_systemd_user_plan(
                plan,
                confirm_operation_id=confirm_operation_id,
                confirm_preview_hash=confirm_preview_hash,
            )
        except ResidentDaemonSystemdUserApplyError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"unit_path: {payload['unit_path']}")
        typer.echo(f"result: {payload['result']}")

    @app_group.command("daemon-systemd-user-status")
    def daemon_systemd_user_status(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_id: Annotated[str | None, typer.Option("--operation-id")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        payload = build_systemd_user_status(
            build_systemd_user_plan(
                runtime_root or _default_runtime_root(),
                host=host,
                port=port,
                operation_id=operation_id,
            )
        )
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"unit_path: {payload['unit_path']}")
        typer.echo(f"active_status: {payload['active_status']}")
        typer.echo(f"enabled_status: {payload['enabled_status']}")

    def _run_control_action(
        *,
        action: str,
        runtime_root: Path | None,
        host: str,
        port: int,
        operation_id: str | None,
        json_out: bool,
    ) -> None:
        plan = build_systemd_user_plan(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
            operation_id=operation_id,
        )
        try:
            payload = run_systemd_user_command(plan, action=action)
        except ResidentDaemonSystemdUserControlError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"action: {payload['action']}")
        typer.echo(f"result: {payload['result']}")

    @app_group.command("daemon-systemd-user-daemon-reload")
    def daemon_systemd_user_daemon_reload(
        runtime_root: Annotated[Path | None, typer.Option("--runtime-root", help="Resident runtime root.")] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_id: Annotated[str | None, typer.Option("--operation-id")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        _run_control_action(
            action="daemon_reload",
            runtime_root=runtime_root,
            host=host,
            port=port,
            operation_id=operation_id,
            json_out=json_out,
        )

    @app_group.command("daemon-systemd-user-enable-now")
    def daemon_systemd_user_enable_now(
        runtime_root: Annotated[Path | None, typer.Option("--runtime-root", help="Resident runtime root.")] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_id: Annotated[str | None, typer.Option("--operation-id")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        _run_control_action(
            action="enable_now",
            runtime_root=runtime_root,
            host=host,
            port=port,
            operation_id=operation_id,
            json_out=json_out,
        )

    @app_group.command("daemon-systemd-user-disable-now")
    def daemon_systemd_user_disable_now(
        runtime_root: Annotated[Path | None, typer.Option("--runtime-root", help="Resident runtime root.")] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        operation_id: Annotated[str | None, typer.Option("--operation-id")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        _run_control_action(
            action="disable_now",
            runtime_root=runtime_root,
            host=host,
            port=port,
            operation_id=operation_id,
            json_out=json_out,
        )
