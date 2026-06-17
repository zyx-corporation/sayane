"""Resident app command registration."""

from __future__ import annotations

import json
import shlex
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from sayane.app import (
    ResidentDaemonLifecycle,
    ResidentDaemonMode,
    build_mcp_preview,
    build_resident_runtime,
    build_review_queue,
)
from sayane.bridge.config import BridgeConfig
from sayane.cli.commands.app_daemon_plans import register_daemon_plan_commands


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
    raise typer.BadParameter(
        "Provide clipboard content via --text, --file, or stdin pipe.",
    )


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
        "repository_backend": runtime.repository_selection.backend.value,
        "storage_boundary": runtime.repository_selection.storage_boundary,
    }


def _daemon_lifecycle(host: str, port: int) -> ResidentDaemonLifecycle:
    try:
        return ResidentDaemonLifecycle(host=host, port=port)
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


def _daemon_status_payload(host: str, port: int) -> dict[str, Any]:
    lifecycle = _daemon_lifecycle(host, port)
    payload = lifecycle.public_metadata()
    payload["kind"] = "resident_daemon_lifecycle_status"
    return payload


def _daemon_plan_payload(host: str, port: int) -> dict[str, Any]:
    lifecycle = _daemon_lifecycle(host, port)
    bridge_command = ["sayane", "serve", "--host", host, "--port", str(port)]
    payload = lifecycle.public_metadata()
    payload.update(
        {
            "kind": "resident_daemon_lifecycle_plan",
            "mode": ResidentDaemonMode.BRIDGE_DELEGATION.value,
            "plan_only": True,
            "daemon_process_started": False,
            "resident_server_implemented": False,
            "current_serve_path": "delegate_to_sayane_serve",
            "bridge_command": bridge_command,
            "bridge_command_text": " ".join(shlex.quote(part) for part in bridge_command),
        },
    )
    return payload


def _empty_review_queue_payload(runtime_profile_id: str) -> dict[str, Any]:
    return {
        "profile_id": runtime_profile_id,
        "kind": "resident_review_queue",
        "is_review_surface": True,
        "is_mcp_context": False,
        "items": [],
        "repository_available": False,
    }


def _empty_mcp_preview_payload(runtime_profile_id: str, *, mode: str) -> dict[str, Any]:
    return {
        "profile_id": runtime_profile_id,
        "mode": mode,
        "is_derived_context": True,
        "is_canonical_profile": False,
        "included_approved_candidates": [],
        "blocked_candidates": [],
        "repository_available": False,
        "preview": {
            "kind": "resident_mcp_preview",
            "is_preview": True,
            "is_derived_context": True,
            "is_canonical_profile": False,
        },
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
        typer.echo(f"repository_backend: {payload['repository_backend']}")
        typer.echo(f"storage_boundary: {payload['storage_boundary']}")
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
            typer.echo(
                json.dumps(candidate.model_dump(mode="json"), ensure_ascii=False, indent=2),
            )
            return
        typer.echo(f"id: {candidate.id}")
        typer.echo(f"status: {candidate.status}")
        typer.echo(f"source: {candidate.source.type}")
        typer.echo(f"section: {candidate.proposal.section}")

    @app_group.command("review-queue")
    def review_queue(
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show the resident review queue preview."""
        runtime = build_resident_runtime()
        if runtime.service.repositories is None:
            payload = _empty_review_queue_payload(runtime.service.profile_id)
        else:
            payload = build_review_queue(
                runtime.service.repositories,
                capability=runtime.capabilities["ui"],
            )
            payload["repository_available"] = True
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"profile_id: {payload['profile_id']}")
        typer.echo(f"items: {len(payload['items'])}")
        typer.echo(f"repository_available: {payload['repository_available']}")

    @app_group.command("mcp-preview")
    def mcp_preview(
        mode: Annotated[str, typer.Option("--mode")] = "full",
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show a derived resident MCP preview payload."""
        runtime = build_resident_runtime()
        if runtime.service.repositories is None:
            payload = _empty_mcp_preview_payload(runtime.service.profile_id, mode=mode)
        else:
            payload = build_mcp_preview(
                runtime.service.repositories,
                capability=runtime.capabilities["mcp"],
                mode=mode,
            )
            payload["repository_available"] = True
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['preview']['kind']}")
        typer.echo(f"profile_id: {payload['profile_id']}")
        typer.echo(f"mode: {payload['mode']}")
        typer.echo(f"repository_available: {payload['repository_available']}")

    @app_group.command("daemon-status")
    def daemon_status(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show resident daemon lifecycle status without starting a daemon."""
        payload = _daemon_status_payload(host, port)
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"state: {payload['state']}")
        typer.echo(f"mode: {payload['mode']}")
        typer.echo(f"is_running_daemon: {payload['is_running_daemon']}")

    @app_group.command("daemon-plan")
    def daemon_plan(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
    ) -> None:
        """Show resident daemon lifecycle plan without starting a daemon."""
        payload = _daemon_plan_payload(host, port)
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"current_serve_path: {payload['current_serve_path']}")
        typer.echo(f"bridge_command: {payload['bridge_command_text']}")
        typer.echo(f"daemon_process_started: {payload['daemon_process_started']}")

    register_daemon_plan_commands(app_group)

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
