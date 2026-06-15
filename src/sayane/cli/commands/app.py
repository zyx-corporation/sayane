"""Resident app command registration."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Annotated

import typer

from sayane.app import build_resident_runtime
from sayane.bridge.config import BridgeConfig


def _read_clipboard_input(text: str | None, file: Path | None) -> str:
    if file is not None and text is not None:
        raise typer.BadParameter("Use either --text or --file, not both.")
    if file is not None:
        if not file.is_file():
            raise typer.BadParameter(f"File not found: {file}")
        return file.read_text(encoding="utf-8").strip()
    if text is not None:
        return text.strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    raise typer.BadParameter("Provide clipboard content via --text, --file, or stdin pipe.")


def _ensure_local_host(host: str) -> None:
    if host not in ("127.0.0.1", "localhost", "::1"):
        raise typer.BadParameter("Resident app serve must bind to localhost.")


def _serve_plan(host: str, port: int) -> dict[str, object]:
    _ensure_local_host(host)
    runtime = build_resident_runtime(host=host, port=port)
    command = ["sayane", "serve", "--host", host, "--port", str(port)]
    return {
        "mode": "delegate_to_sayane_serve",
        "command": command,
        "command_text": " ".join(shlex.quote(part) for part in command),
        "bridge_host": runtime.bridge_config.host,
        "bridge_port": runtime.bridge_config.port,
        "profile_id": runtime.service.profile_id,
        "capabilities": sorted(runtime.capabilities),
    }


def register_app_commands(app: typer.Typer) -> None:
    """Register resident app preparation commands."""
    app_group = typer.Typer(
        name="app",
        help="Resident app preparation commands.",
        no_args_is_help=True,
    )

    @app_group.command("status")
    def status(
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show resident app service boundary status."""
        runtime = build_resident_runtime()
        payload = runtime.describe()
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"profile_id: {payload['profile_id']}")
        typer.echo(f"has_repositories: {payload['has_repositories']}")
        typer.echo(f"candidate_repository: {payload['candidate_repository']}")
        typer.echo(f"review_decision_repository: {payload['review_decision_repository']}")
        typer.echo(f"lineage_repository: {payload['lineage_repository']}")
        typer.echo(f"bridge_host: {payload['bridge_host']}")
        typer.echo(f"bridge_port: {payload['bridge_port']}")
        typer.echo(f"capabilities: {', '.join(payload['capabilities'])}")

    @app_group.command("capture-clipboard")
    def capture_clipboard(
        text: Annotated[str | None, typer.Option("--text", help="Clipboard text.")] = None,
        file: Annotated[
            Path | None,
            typer.Option("--file", "-f", help="Read clipboard text from a file."),
        ] = None,
        locale: Annotated[str | None, typer.Option("--locale")] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Capture explicit clipboard text as a pending Candidate."""
        content = _read_clipboard_input(text, file)
        if not content:
            raise typer.BadParameter("Clipboard content is empty.")

        runtime = build_resident_runtime()
        candidate = runtime.service.capture_clipboard_as_candidate(
            content,
            capability=runtime.capabilities["capture"],
            config=runtime.bridge_config,
            locale=locale,
        )
        if json_out:
            typer.echo(json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False, indent=2))
            return
        typer.echo(f"id: {candidate.id}")
        typer.echo(f"status: {candidate.status}")
        typer.echo(f"source: {candidate.source.type}")
        typer.echo(f"section: {candidate.proposal.section}")

    @app_group.command("serve")
    def serve(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the resident app serve delegation plan."""
        payload = _serve_plan(host, port)
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo("Resident app serve delegates to the existing Bridge command:")
        typer.echo(str(payload["command_text"]))

    app.add_typer(app_group)
