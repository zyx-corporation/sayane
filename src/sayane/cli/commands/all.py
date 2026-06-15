"""Built-in Sayane CLI command registration."""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import typer

from sayane.cli.commands.app import register_app_commands
from sayane.cli.commands.candidate import register_candidate
from sayane.cli.commands.capture import register_capture
from sayane.cli.commands.core import register_core_commands
from sayane.cli.commands.export import register_export
from sayane.cli.commands.import_bundle import register_import_bundle
from sayane.cli.commands.mcp import register_mcp
from sayane.cli.commands.package import register_package_commands
from sayane.cli.commands.profile import register_profile
from sayane.cli.commands.review import register_review
from sayane.cli.commands.storage import register_storage

LoadProfile = Callable[[Path | None], tuple[Path, object]]


def register_builtin_commands(
    app: typer.Typer,
    load_profile_fn: LoadProfile,
    init_template: str,
) -> None:
    """Register built-in commands in the same order as the legacy CLI app.

    This helper is intentionally small and ordering-focused. It allows
    ``sayane.cli.app`` to become an assembly point without changing command
    names, options, or output text.
    """
    register_profile(app, load_profile_fn)
    register_core_commands(app, load_profile_fn, init_template)
    register_app_commands(app)
    register_capture(app)
    register_export(app, load_profile_fn)
    register_import_bundle(app, load_profile_fn)
    register_review(app)
    register_package_commands(app)
    register_candidate(app)
    register_storage(app)
    register_mcp(app)
