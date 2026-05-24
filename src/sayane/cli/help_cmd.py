"""Hierarchical help for the Sayane CLI."""

from __future__ import annotations

from typing import Annotated

import click
import typer
from typer.main import get_command

import sayane
from sayane.cli.i18n import t


def register_help(app: typer.Typer) -> None:
    """Register top-level ``sayane help [TOPIC...]``."""

    @app.command("help")
    def help_command(
        topics: Annotated[
            list[str] | None,
            typer.Argument(
                help="Command path (e.g. candidate, candidate evaluate, mcp serve).",
            ),
        ] = None,
    ) -> None:
        """Show hierarchical help for commands and groups."""
        try:
            typer.echo(render_help(topics))
        except HelpTopicError as exc:
            raise typer.BadParameter(str(exc)) from exc


def render_help(topics: list[str] | None) -> str:
    """Return help text for a topic path or the root overview."""
    from sayane.cli.app import build_app

    root = get_command(build_app())
    ctx = click.Context(root, info_name="sayane")
    path = topics or []

    if not path:
        return _format_overview(root, ctx)

    cmd: click.Command = root
    for part in path:
        if not isinstance(cmd, click.Group):
            raise HelpTopicError(
                t("help.not_group", part=part, path=" ".join(path)),
            )
        sub = cmd.get_command(ctx, part)
        if sub is None:
            raise HelpTopicError(
                t("help.unknown_topic", part=part, path=" ".join(path)),
            )
        ctx = click.Context(sub, parent=ctx, info_name=part)
        cmd = sub

    return cmd.get_help(ctx)


class HelpTopicError(Exception):
    """Invalid help topic path."""


def _format_overview(group: click.Group, ctx: click.Context) -> str:
    lines = [
        t("help.tagline", version=sayane.__version__),
        "",
        t("help.usage_title"),
        t("help.usage_help"),
        t("help.usage_group"),
        t("help.usage_cmd"),
        "",
        t("help.topics_title"),
        t("help.topic1"),
        t("help.topic2"),
        t("help.topic3"),
        "",
    ]

    commands: list[tuple[str, str]] = []
    groups: list[tuple[str, str, list[tuple[str, str]]]] = []

    for name in sorted(group.list_commands(ctx)):
        sub = group.get_command(ctx, name)
        if sub is None:
            continue
        summary = _first_line(sub.help)
        if isinstance(sub, click.Group):
            sub_ctx = click.Context(sub, parent=ctx, info_name=name)
            children = []
            for child_name in sorted(sub.list_commands(sub_ctx)):
                child = sub.get_command(sub_ctx, child_name)
                if child is not None:
                    children.append((child_name, _first_line(child.help)))
            groups.append((name, summary, children))
        else:
            commands.append((name, summary))

    if commands:
        lines.append(t("help.commands_title"))
        for name, summary in commands:
            lines.append(f"  {name:<12} {summary}")
        lines.append("")

    if groups:
        lines.append(t("help.groups_title"))
        for name, summary, children in groups:
            lines.append(f"  {name:<12} {summary}")
            for child_name, child_summary in children:
                lines.append(f"    {child_name:<14} {child_summary}")
        lines.append("")

    lines.append(t("help.docs"))
    return "\n".join(lines)


def _first_line(help_text: str | None) -> str:
    if not help_text:
        return ""
    return help_text.strip().split("\n")[0]
