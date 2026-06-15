"""Export command registration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Callable

import typer

from sayane.cli.i18n import t

LoadProfile = Callable[[Path | None], tuple[Path, object]]


def register_export(app: typer.Typer, load_profile_fn: LoadProfile) -> None:
    """Register the export command on the given Typer app."""

    @app.command()
    def export(
        format: Annotated[str, typer.Option("--format")],
        target: Annotated[str, typer.Option("--target")] = "chatgpt",
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        scope: Annotated[str | None, typer.Option("--scope", help="Comma-separated scopes: identity,interaction,technical,...")] = None,
    ) -> None:
        """Export profile context in yaml, markdown, or prompt format."""
        from sayane.core.export import export_markdown, export_prompt, export_yaml

        _path, loaded = load_profile_fn(profile)
        scopes = [s.strip() for s in scope.split(",") if s.strip()] if scope else ["identity", "interaction"]

        if format == "yaml":
            typer.echo(export_yaml(loaded, scopes))
        elif format == "markdown":
            typer.echo(export_markdown(loaded, scopes, target))
        elif format == "prompt":
            typer.echo(export_prompt(loaded, scopes, target))
        else:
            raise typer.BadParameter(t("error.unsupported_format", format=format))
