"""Capture command registration."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Annotated

import typer

from sayane.bridge.config import BridgeConfig


def register_capture(app: typer.Typer) -> None:
    """Register the capture command on the given Typer app."""

    @app.command()
    def capture(
        text: Annotated[str | None, typer.Option("--text", help="Capture body text.")] = None,
        file: Annotated[
            Path | None,
            typer.Option("--file", "-f", help="Read capture body from a file."),
        ] = None,
        source: Annotated[str | None, typer.Option("--source", help="Source label.")] = None,
        source_url: Annotated[str | None, typer.Option("--source-url")] = None,
        section: Annotated[
            str | None,
            typer.Option("--section", help="Target profile section (e.g. knowledge.concepts)."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON response.")] = False,
    ) -> None:
        """Save captured text as a pending Candidate (same as Bridge POST /capture)."""
        from sayane.bridge.capture_store import save_capture
        from sayane.bridge.models import CaptureRequest

        if file is not None and text is not None:
            raise typer.BadParameter("Use either --text or --file, not both.")
        if file is not None:
            if not file.is_file():
                raise typer.BadParameter(f"File not found: {file}")
            content = file.read_text(encoding="utf-8")
        elif text is not None:
            content = text
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            typer.echo(
                "Provide capture content via --text, --file, or stdin pipe.",
                err=True,
            )
            raise typer.Exit(2)

        content = content.strip()
        if not content:
            raise typer.BadParameter("Capture content is empty.")

        try:
            response = save_capture(
                BridgeConfig(),
                CaptureRequest(
                    content=content,
                    source=source or "cli",
                    source_url=source_url,
                    section=section,
                ),
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

        if json_out:
            typer.echo(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))
            return

        typer.echo(f"id: {response.id}")
        typer.echo(f"path: {response.path}")
        typer.echo(f"status: {response.status}")
        for warning in response.warnings:
            typer.echo(f"warning: {warning}", err=True)
