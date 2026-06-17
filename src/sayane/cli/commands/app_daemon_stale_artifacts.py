"""Read-only resident daemon stale artifact diagnostic CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import (
    ResidentDaemonIdentity,
    ResidentDaemonRuntimeLayout,
    build_stale_artifact_report,
)
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def build_stale_artifact_payload(runtime_root: Path | None = None) -> dict[str, object]:
    """Build a read-only stale artifact diagnostic preview payload."""
    root = runtime_root or _default_runtime_root()
    identity = ResidentDaemonIdentity(runtime_dir=root)
    layout = ResidentDaemonRuntimeLayout(runtime_root=root)
    return build_stale_artifact_report(identity=identity, layout=layout).public_metadata()


def register_daemon_stale_artifact_command(app_group: typer.Typer) -> None:
    """Register read-only stale artifact diagnostic preview command."""

    @app_group.command("daemon-stale-artifacts")
    def daemon_stale_artifacts(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show stale daemon artifact diagnostics without mutating files."""
        try:
            payload = build_stale_artifact_payload(runtime_root)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"runtime_root: {payload['runtime_root']}")
        typer.echo(f"stale_artifact_policy: {payload['stale_artifact_policy']}")
        typer.echo(f"manual_review_required: {payload['manual_review_required']}")
        typer.echo(f"mutates_filesystem: {payload['mutates_filesystem']}")
        typer.echo(f"diagnostics: {len(payload['diagnostics'])}")
