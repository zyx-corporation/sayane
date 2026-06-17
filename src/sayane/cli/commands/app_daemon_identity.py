"""Read-only resident daemon identity CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import ResidentDaemonIdentity
from sayane.bridge.config import BridgeConfig


def _default_runtime_dir() -> Path:
    return BridgeConfig().home / "run"


def build_identity_payload(runtime_dir: Path | None = None) -> dict[str, object]:
    """Build a read-only daemon identity preview payload."""
    identity = ResidentDaemonIdentity(runtime_dir=runtime_dir or _default_runtime_dir())
    payload = identity.public_metadata()
    payload["kind"] = "resident_daemon_identity_preview"
    payload["preview_only"] = True
    return payload


def register_daemon_identity_command(app_group: typer.Typer) -> None:
    """Register read-only resident daemon identity preview command."""

    @app_group.command("daemon-identity")
    def daemon_identity(
        runtime_dir: Annotated[
            Path | None,
            typer.Option("--runtime-dir", help="Override resident runtime directory."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show daemon identity paths without writing files or acquiring locks."""
        try:
            payload = build_identity_payload(runtime_dir)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"pid_path: {payload['pid_path']}")
        typer.echo(f"lock_path: {payload['lock_path']}")
        typer.echo(f"writes_files: {payload['writes_files']}")
        typer.echo(f"acquires_lock: {payload['acquires_lock']}")
