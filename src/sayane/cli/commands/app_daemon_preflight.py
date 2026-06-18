"""Resident daemon implementation preflight CLI helper."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from sayane.app import build_implementation_gate_preflight_report, build_preflight_event_record


def build_preflight_payload(*, include_event_record: bool = False) -> dict[str, object]:
    """Build schema-only implementation gate preflight payload."""
    report = build_implementation_gate_preflight_report()
    payload = report.public_metadata()
    if include_event_record:
        payload["event_record"] = build_preflight_event_record(report).public_metadata()
    return payload


def register_daemon_preflight_command(app_group: typer.Typer) -> None:
    """Register resident daemon implementation preflight preview command."""

    @app_group.command("daemon-preflight")
    def daemon_preflight(
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON output.")] = False,
        include_event_record: Annotated[
            bool,
            typer.Option(
                "--include-event-record",
                help="Include a schema-only preview event record in the payload.",
            ),
        ] = False,
    ) -> None:
        """Show resident daemon implementation gate preflight without side effects."""
        payload = build_preflight_payload(include_event_record=include_event_record)
        if json_out:
            typer.echo(json.dumps(payload, ensure_ascii=False, indent=2))
            return
        typer.echo(f"kind: {payload['kind']}")
        typer.echo(f"target_scope: {payload['target_scope']}")
        typer.echo(f"status: {payload['status']}")
        typer.echo(f"items: {len(payload['items'])}")
        typer.echo(f"mutates_filesystem: {payload['mutates_filesystem']}")
        typer.echo(f"probes_process: {payload['probes_process']}")
        typer.echo(f"controls_process: {payload['controls_process']}")
        typer.echo(f"exposes_ipc: {payload['exposes_ipc']}")
        typer.echo(f"integrates_os_service: {payload['integrates_os_service']}")
        if include_event_record:
            event_record = payload["event_record"]
            typer.echo(f"event_record.kind: {event_record['kind']}")
            typer.echo(f"event_record.result: {event_record['result']}")
