"""Small text-output helpers for CLI summary commands."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Callable

import typer


def echo_list_section(title: str, items: Iterable[Any]) -> None:
    """Emit a simple indented bullet list."""
    values = list(items)
    typer.echo(f"{title}:")
    if not values:
        typer.echo("  - —")
        return
    for item in values:
        typer.echo(f"  - {item}")


def echo_object_section(
    title: str,
    items: Iterable[Any],
    formatter: Callable[[Any], str],
) -> None:
    """Emit a simple indented bullet list from structured items."""
    values = list(items)
    typer.echo(f"{title}:")
    if not values:
        typer.echo("  - —")
        return
    for item in values:
        typer.echo(f"  - {formatter(item)}")
