"""Discover optional CLI extensions (Commercial Edition plugins, etc.)."""

from __future__ import annotations

from importlib.metadata import entry_points

import typer


def register_cli_extensions(app: typer.Typer) -> None:
    from sayane.cli.vault_cmd import register_vault_cli
    from sayane.plugins.hooks import ensure_hooks_loaded

    register_vault_cli(app)
    ensure_hooks_loaded()
    try:
        eps = entry_points(group="sayane.cli_extensions")
    except TypeError:
        eps = entry_points().get("sayane.cli_extensions", ())
    for ep in eps:
        register = ep.load()
        register(app)
