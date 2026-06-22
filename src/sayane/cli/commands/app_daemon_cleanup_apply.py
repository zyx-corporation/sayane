"""Resident daemon cleanup apply CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    ResidentDaemonCleanupApplyError,
    ResidentDaemonCleanupApplyTarget,
    apply_cleanup_decisions,
    build_cleanup_apply_preview,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_cleanup_apply_command(app_group: typer.Typer) -> None:
    """Register conservative cleanup-apply command."""

    @app_group.command("daemon-cleanup-preview")
    def daemon_cleanup_preview(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the current cleanup-apply preview with confirmation fields."""
        payload = build_cleanup_apply_preview(
            runtime_root or _default_runtime_root(),
            host=host,
            port=port,
        )
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"operation_id: {payload['operation_id']}")
        typer.echo(f"preview_hash: {payload['preview_hash']}")

    @app_group.command("daemon-cleanup-apply")
    def daemon_cleanup_apply(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        remove: Annotated[
            list[ResidentDaemonCleanupApplyTarget],
            typer.Option(
                "--remove",
                help="Explicit artifact target to remove. Repeatable: pid_file, lock_file, socket_file.",
            ),
        ] = [],
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        confirm_operation_id: Annotated[
            str | None,
            typer.Option(
                "--confirm-operation-id",
                help="Repeat the cleanup preview operation id before mutation.",
            ),
        ] = None,
        confirm_preview_hash: Annotated[
            str | None,
            typer.Option(
                "--confirm-preview-hash",
                help="Repeat the cleanup preview hash before mutation.",
            ),
        ] = None,
        include_event_record: Annotated[
            bool,
            typer.Option(
                "--include-event-record",
                help="Include a derived resident daemon event record in the payload.",
            ),
        ] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Apply conservative file cleanup to explicit stale runtime targets."""
        try:
            payload = apply_cleanup_decisions(
                runtime_root or _default_runtime_root(),
                targets=tuple(remove),
                host=host,
                port=port,
                confirm_operation_id=confirm_operation_id,
                confirm_preview_hash=confirm_preview_hash,
                include_event_record=include_event_record,
            )
        except ResidentDaemonCleanupApplyError as exc:
            if json_out:
                typer.echo(json.dumps(exc.payload, ensure_ascii=False, indent=2))
                raise typer.Exit(1) from exc
            raise typer.BadParameter(str(exc)) from exc

        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"result: {payload['result']}")
        typer.echo(f"applied: {payload['applied']}")
        typer.echo(f"removed_paths: {len(payload['removed_paths'])}")
