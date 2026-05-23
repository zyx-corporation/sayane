"""CLI access to Omomuki MCP operations (same handlers as MCP server tools)."""

import json
from typing import Annotated

import typer

from omomuki.mcp.operations import get_operations

mcp_app = typer.Typer(
    help="MCP Server tools and stdio server (read-only).",
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
