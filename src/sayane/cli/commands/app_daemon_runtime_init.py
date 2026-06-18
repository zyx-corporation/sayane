"""Resident daemon runtime initialization CLI helper."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import apply_runtime_init, build_runtime_init_plan
from sayane.bridge.config import BridgeConfig


def _default_runtime_root() -> Path:
    return BridgeConfig().home / "run"


def register_daemon_runtime_init_command(app_group: typer.Typer) -> None:
    """Register explicit runtime initialization command."""

    @app_group.command("daemon-runtime-init")
    def daemon_runtime_init(
        runtime_root: Annotated[
            Path | None,
            typer.Option("--runtime-root", help="Override resident runtime root."),
        ] = None,
        apply: Annotated[
            bool,
            typer.Option("--apply", help="Create the missing runtime directories."),
        ] = False,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Preview or apply minimal resident runtime directory creation."""
        plan = build_runtime_init_plan(runtime_root or _default_runtime_root())
        if apply:
            try:
                payload = apply_runtime_init(plan)
            except ValueError as exc:
                raise typer.BadParameter(str(exc)) from exc
        else:
            payload = plan.public_metadata()
            payload["preview_only"] = True
            payload["mutates_filesystem"] = False

        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return

        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"runtime_root: {payload['runtime_root']}")
        typer.echo(f"review_required: {payload['review_required']}")
        typer.echo(
            f"explicit_operator_intent_required: {payload['explicit_operator_intent_required']}"
        )
        if "created_paths" in payload:
            typer.echo(f"created_paths: {len(payload['created_paths'])}")
