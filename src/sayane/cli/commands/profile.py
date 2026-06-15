"""Profile command group registration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Callable

import typer

from sayane.bridge.config import BridgeConfig
from sayane.cli.i18n import t

LoadProfile = Callable[[Path | None], tuple[Path, object]]


def register_profile(app: typer.Typer, load_profile_fn: LoadProfile) -> None:
    """Register profile commands on the given Typer app."""
    profile_app = typer.Typer(help=t("group.profile"), no_args_is_help=True)

    @profile_app.command("inspect")
    def profile_inspect(
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Show a summary of the loaded profile."""
        path, loaded = load_profile_fn(profile)
        p = loaded
        typer.echo(t("inspect.path", path=path))
        typer.echo(t("inspect.kind", kind=p.kind, version=p.version))
        typer.echo(
            t(
                "inspect.identity",
                name=p.identity.name,
                preferred=p.identity.preferred_name or "-",
            ),
        )
        if p.identity.roles:
            typer.echo(t("inspect.roles", roles=", ".join(p.identity.roles)))
        if p.voice.tone:
            typer.echo(t("inspect.tone", tone=", ".join(p.voice.tone)))
        if p.values.core:
            typer.echo(t("inspect.values", values=", ".join(p.values.core)))
        if p.knowledge and p.knowledge.concepts:
            typer.echo(t("inspect.concepts", concepts=", ".join(p.knowledge.concepts)))
        if p.context_index.entrypoint:
            typer.echo(t("inspect.entrypoint", path=p.context_index.entrypoint))
        from sayane.core.profile_quality import validate_profile_quality

        for warning in validate_profile_quality(p):
            typer.echo(f"warning: {warning}", err=True)

    @profile_app.command("validate")
    def profile_validate(
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Check profile layout (tone, concepts, PII placement)."""
        _path, loaded = load_profile_fn(profile)
        from sayane.core.profile_quality import validate_profile_quality

        warnings = validate_profile_quality(loaded)
        if not warnings:
            typer.echo("Profile layout: OK")
            return
        typer.echo("Profile layout warnings:", err=True)
        for warning in warnings:
            typer.echo(f"  - {warning}", err=True)
        raise typer.Exit(1)

    @profile_app.command("diff")
    def profile_diff(
        candidate_id: Annotated[str, typer.Option("--candidate")],
    ) -> None:
        """Show profile diff for a candidate."""
        from sayane.evaluators.service import diff_candidate

        diff = diff_candidate(BridgeConfig(), candidate_id)
        typer.echo(json.dumps(diff, ensure_ascii=False, indent=2))

    app.add_typer(profile_app, name="profile")
