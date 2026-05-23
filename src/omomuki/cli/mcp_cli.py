"""CLI access to Omomuki MCP operations (same handlers as MCP server tools)."""

import json
from typing import Annotated

import typer

from omomuki.mcp.operations import get_operations

mcp_app = typer.Typer(
    help="MCP Server tools and stdio server.",
    no_args_is_help=True,
)


def _echo_json(data: object) -> None:
    typer.echo(json.dumps(data, ensure_ascii=False, indent=2))


@mcp_app.command("serve")
def mcp_serve() -> None:
    """Start the Omomuki MCP server on stdio (for Cursor / Claude Desktop / Cline)."""
    from omomuki.mcp.server import run_stdio

    typer.echo("Starting Omomuki MCP server (stdio)...", err=True)
    run_stdio()


@mcp_app.command("list-profiles")
def mcp_list_profiles() -> None:
    """List profiles (same as MCP tool list_profiles)."""
    _echo_json(get_operations().list_profiles())


@mcp_app.command("inspect-profile")
def mcp_inspect_profile(
    profile_id: Annotated[
        str,
        typer.Option("--profile-id", help="Profile id under ~/.omomuki/profiles/"),
    ] = "default",
) -> None:
    """Show profile summary (same as MCP tool inspect_profile)."""
    try:
        _echo_json(get_operations().inspect_profile(profile_id=profile_id))
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("compile")
def mcp_compile(
    target: Annotated[str, typer.Option("--target", help="chatgpt or claude")],
    profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
    instruction: Annotated[str | None, typer.Option("--instruction")] = None,
) -> None:
    """Compile prompt (same as MCP tool compile_prompt)."""
    try:
        _echo_json(
            get_operations().compile_prompt(
                target=target,
                profile_id=profile_id,
                instruction=instruction,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("context-packet")
def mcp_context_packet(
    target: Annotated[str, typer.Option("--target", help="chatgpt or claude")],
    profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
    instruction: Annotated[str | None, typer.Option("--instruction")] = None,
) -> None:
    """Generate context packet (same as MCP tool generate_context_packet)."""
    try:
        _echo_json(
            get_operations().generate_context_packet(
                target=target,
                profile_id=profile_id,
                instruction=instruction,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("list-candidates")
def mcp_list_candidates() -> None:
    """List candidate captures (same as MCP tool list_candidate_updates)."""
    _echo_json(get_operations().list_candidate_updates())


@mcp_app.command("show-candidate")
def mcp_show_candidate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
    """Show candidate record (same as MCP tool show_candidate)."""
    try:
        _echo_json(get_operations().show_candidate(candidate_id))
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("evaluate-candidate")
def mcp_evaluate_candidate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
    level: Annotated[int, typer.Option("--level", min=1, max=3)] = 1,
) -> None:
    """Evaluate candidate (same as MCP tool evaluate_candidate)."""
    try:
        _echo_json(get_operations().evaluate_candidate(candidate_id, level=level))
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("approve-candidate")
def mcp_approve_candidate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
    force_critical: Annotated[bool, typer.Option("--force-critical")] = False,
) -> None:
    """Approve and merge candidate (same as MCP tool approve_candidate)."""
    try:
        _echo_json(
            get_operations().approve_candidate(
                candidate_id,
                force_critical=force_critical,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("reject-candidate")
def mcp_reject_candidate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
    reason: Annotated[str | None, typer.Option("--reason")] = None,
) -> None:
    """Reject candidate (same as MCP tool reject_candidate)."""
    try:
        _echo_json(get_operations().reject_candidate(candidate_id, reason=reason))
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc


@mcp_app.command("diff-candidate")
def mcp_diff_candidate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
    """Diff candidate vs profile (same as MCP tool diff_candidate)."""
    try:
        _echo_json(get_operations().diff_candidate(candidate_id))
    except FileNotFoundError as exc:
        raise typer.BadParameter(str(exc)) from exc
