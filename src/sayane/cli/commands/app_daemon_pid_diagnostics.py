"""Read-only resident daemon PID file diagnostic CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def build_pid_file_diagnostic_payload(runtime_root: Path | None = None) -> dict[str, object]:
    """Build a read-only PID file parse diagnostic preview payload."""
    from sayane.app import ResidentDaemonIdentity, build_pid_file_diagnostic

    root = runtime_root or _default_runtime_root()
    identity = ResidentDaemonIdentity(runtime_dir=root)
    return build_pid_file_diagnostic(identity).public_metadata()


def register_daemon_pid_diagnostic_command(app_group: typer.Typer) -> None:
    """Register read-only PID file diagnostic preview command."""

    @app_group.command("daemon-pid-diagnostic")
    def daemon_pid_diagnostic(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Parse the planned daemon PID file without controlling processes."""
        try:
            payload = build_pid_file_diagnostic_payload(runtime_root)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"path: {payload['path']}")
        typer.echo(f"status: {payload['status']}")
        typer.echo(f"parsed_pid: {payload['parsed_pid']}")
        typer.echo(f"manual_review_required: {payload['manual_review_required']}")
        typer.echo(f"proves_liveness: {payload['proves_liveness']}")
        typer.echo(f"mutates_filesystem: {payload['mutates_filesystem']}")
