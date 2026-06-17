"""Build Sayane Typer application (locale-aware)."""

from __future__ import annotations

from importlib import metadata
from pathlib import Path
from typing import Annotated

import typer

from sayane.cli.commands.all import register_builtin_commands
from sayane.cli.help_cmd import register_help
from sayane.cli.i18n import t
from sayane.cli.paths import resolve_profile_path
from sayane.core.loader import load_profile

INIT_TEMPLATE = """\
version: "0.1.0"
kind: "SayaneProfile"
identity:
  name: "Your Name"
  preferred_name: ""
  roles: []
voice:
  default_language: "ja"
  tone: []
values:
  core: []
knowledge:
  concepts: []
policy:
  response:
    avoid: []
    prefer: []
context_index:
  entrypoint: "context/MyContext.md"
  handoff: "context/AI_HANDOFF.md"
lineage:
  created_at: "{now}"
  updated_at: "{now}"
"""


def _package_version() -> str:
    try:
        return metadata.version("sayane")
    except metadata.PackageNotFoundError:
        return "0+unknown"


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sayane {_package_version()}")
        raise typer.Exit()


def build_app() -> typer.Typer:
    """Construct CLI app using the active locale."""
    app = typer.Typer(
        no_args_is_help=True,
        help=t("app.help"),
        rich_markup_mode="markdown",
    )

    @app.callback()
    def _global_options(
        lang: Annotated[
            str | None,
            typer.Option(
                "--lang",
                help=t("lang.option_help"),
                envvar="SAYANE_LANG",
            ),
        ] = None,
        version: Annotated[
            bool | None,
            typer.Option(
                "--version",
                "-V",
                callback=_version_callback,
                is_eager=True,
                help="Show version and exit.",
            ),
        ] = None,
    ) -> None:
        """Global options (locale is applied before Typer runs via main())."""
        del lang, version

    register_builtin_commands(app, _load, INIT_TEMPLATE)
    register_help(app)

    from sayane.cli.plugins import register_cli_extensions

    register_cli_extensions(app)
    return app


def _load(profile: Path | None) -> tuple[Path, object]:
    path = resolve_profile_path(profile)
    if not path.exists():
        raise typer.BadParameter(t("error.profile_not_found", path=path))
    return path, load_profile(path)
