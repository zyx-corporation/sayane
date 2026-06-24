"""MCP command group registration."""

from __future__ import annotations

import json
from typing import Annotated

import typer

from sayane.cli.i18n import t


def register_mcp(app: typer.Typer) -> None:
    """Register MCP commands on the given Typer app."""
    mcp_app = typer.Typer(help=t("group.mcp"), no_args_is_help=True)

    def _echo_json(data: object) -> None:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))

    def _get_operations():
        from sayane.mcp.operations import get_operations

        return get_operations()

    @mcp_app.command("serve")
    def mcp_serve() -> None:
        """Start MCP server on stdio."""
        from sayane.mcp.server import run_stdio

        typer.echo(t("mcp.starting"), err=True)
        run_stdio()

    @mcp_app.command("list-profiles")
    def mcp_list_profiles() -> None:
        _echo_json(_get_operations().list_profiles())

    @mcp_app.command("inspect-profile")
    def mcp_inspect_profile(
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
    ) -> None:
        try:
            _echo_json(_get_operations().inspect_profile(profile_id=profile_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("compile")
    def mcp_compile(
        target: Annotated[str, typer.Option("--target")],
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
        ) -> None:
        try:
            _echo_json(
                _get_operations().compile_prompt(
                    target=target,
                    profile_id=profile_id,
                    instruction=instruction,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("context-packet")
    def mcp_context_packet(
        target: Annotated[str, typer.Option("--target")],
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
        ) -> None:
        try:
            _echo_json(
                _get_operations().generate_context_packet(
                    target=target,
                    profile_id=profile_id,
                    instruction=instruction,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("list-candidates")
    def mcp_list_candidates() -> None:
        _echo_json(_get_operations().list_candidate_updates())

    @mcp_app.command("show-candidate")
    def mcp_show_candidate(candidate_id: Annotated[str, typer.Argument()]) -> None:
        try:
            _echo_json(_get_operations().show_candidate(candidate_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("evaluate-candidate")
    def mcp_evaluate_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        level: Annotated[int, typer.Option("--level", min=1, max=3)] = 1,
    ) -> None:
        try:
            _echo_json(_get_operations().evaluate_candidate(candidate_id, level=level))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("approve-candidate")
    def mcp_approve_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        force_critical: Annotated[bool, typer.Option("--force-critical")] = False,
    ) -> None:
        try:
            _echo_json(
                _get_operations().approve_candidate(
                    candidate_id,
                    force_critical=force_critical,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("reject-candidate")
    def mcp_reject_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        reason: Annotated[str | None, typer.Option("--reason")] = None,
    ) -> None:
        try:
            _echo_json(_get_operations().reject_candidate(candidate_id, reason=reason))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("diff-candidate")
    def mcp_diff_candidate(candidate_id: Annotated[str, typer.Argument()]) -> None:
        try:
            _echo_json(_get_operations().diff_candidate(candidate_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    app.add_typer(mcp_app, name="mcp")
