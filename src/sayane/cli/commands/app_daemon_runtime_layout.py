"""Read-only resident daemon runtime layout CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import ResidentDaemonRuntimeLayout
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def build_runtime_layout_payload(runtime_root: Path | None = None) -> dict[str, object]:
    """Build a read-only daemon runtime layout preview payload."""
    layout = ResidentDaemonRuntimeLayout(runtime_root=runtime_root or _default_runtime_root())
    payload = layout.public_metadata()
    payload["kind"] = "resident_daemon_runtime_layout_preview"
    payload["preview_only"] = True
    return payload


def register_daemon_runtime_layout_command(app_group: typer.Typer) -> None:
    """Register read-only resident daemon runtime layout preview command."""

    @app_group.command("daemon-runtime-layout")
    def daemon_runtime_layout(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show daemon runtime layout paths without touching the filesystem."""
        try:
            payload = build_runtime_layout_payload(runtime_root)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"runtime_root: {payload['runtime_root']}")
        typer.echo(f"pid_dir: {payload['pid_dir']}")
        typer.echo(f"lock_dir: {payload['lock_dir']}")
        typer.echo(f"socket_dir: {payload['socket_dir']}")
        typer.echo(f"creates_directories: {payload['creates_directories']}")
        typer.echo(f"writes_files: {payload['writes_files']}")
