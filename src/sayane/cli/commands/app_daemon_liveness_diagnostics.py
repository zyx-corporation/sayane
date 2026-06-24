"""Read-only resident daemon liveness diagnostic CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def build_liveness_diagnostic_payload(runtime_root: Path | None = None) -> dict[str, object]:
    """Build a read-only liveness diagnostic preview payload."""
    from sayane.app import ResidentDaemonIdentity, build_liveness_diagnostic

    root = runtime_root or _default_runtime_root()
    identity = ResidentDaemonIdentity(runtime_dir=root)
    return build_liveness_diagnostic(identity).public_metadata()


def register_daemon_liveness_diagnostic_command(app_group: typer.Typer) -> None:
    """Register read-only liveness diagnostic preview command."""

    @app_group.command("daemon-liveness-diagnostic")
    def daemon_liveness_diagnostic(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Report resident daemon liveness evidence without probing processes."""
        try:
            payload = build_liveness_diagnostic_payload(runtime_root)
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"status: {payload['status']}")
        typer.echo(f"evidence_ceiling: {payload['evidence_ceiling']}")
        typer.echo(f"manual_review_required: {payload['manual_review_required']}")
        typer.echo(f"proves_liveness: {payload['proves_liveness']}")
        typer.echo(f"probes_process: {payload['probes_process']}")
        typer.echo(f"controls_process: {payload['controls_process']}")
        typer.echo(f"mutates_filesystem: {payload['mutates_filesystem']}")
