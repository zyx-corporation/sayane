"""CLI for Phase 5 storage: Obsidian, context index, Git."""

from pathlib import Path
from typing import Annotated

import typer

from omomuki.cli.paths import resolve_profile_path
from omomuki.core.loader import save_profile
from omomuki.storage.context_index import apply_context_index
from omomuki.storage.filesystem import FileSystemContextStore, FileSystemProfileStore
from omomuki.storage.git_integration import GitError, commit_profile_store
from omomuki.storage.obsidian import export_to_vault, import_from_vault

storage_app = typer.Typer(help="Storage: Obsidian import/export, context index, Git.")


def _profile_store(profile: Path | None) -> FileSystemProfileStore:
    path = resolve_profile_path(profile)
    if not path.exists():
        raise typer.BadParameter(f"Profile not found: {path}. Run `omomuki init` first.")
    return FileSystemProfileStore(path.parent)


@storage_app.command("import")
def storage_import(
    vault: Annotated[Path, typer.Argument(help="Obsidian vault directory")],
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="List files only; do not copy"),
    ] = False,
) -> None:
    """Import markdown from an Obsidian vault into the profile context store."""
    from omomuki.storage.obsidian import iter_vault_markdown

    store = _profile_store(profile)
    ctx = FileSystemContextStore(store.profile_dir)

    if dry_run:
        paths = iter_vault_markdown(vault)
        for p in paths:
            rel = p.relative_to(vault.resolve()).as_posix()
            typer.echo(rel)
        typer.echo(f"Would import {len(paths)} file(s)")
        return

    imported = import_from_vault(vault, ctx.context_dir)
    profile_obj = apply_context_index(store.load(), store.profile_dir)
    save_profile(store.profile_path, profile_obj)
    typer.echo(f"Imported {len(imported)} file(s) into {ctx.context_dir}")
    typer.echo("Updated context_index in profile")


@storage_app.command("export")
def storage_export(
    vault: Annotated[Path, typer.Argument(help="Obsidian vault directory")],
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
    subdir: Annotated[
        str,
        typer.Option("--subdir", help="Subdirectory under vault for export"),
    ] = "omomuki",
) -> None:
    """Export profile context markdown into vault/<subdir>/."""
    store = _profile_store(profile)
    ctx = FileSystemContextStore(store.profile_dir)
    exported = export_to_vault(ctx.context_dir, vault, subdir=subdir)
    typer.echo(f"Exported {len(exported)} file(s) under {vault / subdir}")


@storage_app.command("index")
def storage_index(
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
) -> None:
    """Regenerate context_index.entries from context/ markdown files."""
    store = _profile_store(profile)
    profile_obj = apply_context_index(store.load(), store.profile_dir)
    save_profile(store.profile_path, profile_obj)
    idx = profile_obj.context_index
    typer.echo(f"entrypoint: {idx.entrypoint}")
    typer.echo(f"handoff: {idx.handoff}")
    typer.echo(f"entries: {len(idx.entries)}")


@storage_app.command("commit")
def storage_commit(
    message: Annotated[str, typer.Option("-m", "--message", help="Commit message")],
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
    init: Annotated[
        bool,
        typer.Option("--init", help="Run git init if profile dir is not a repo"),
    ] = False,
) -> None:
    """Commit profile and context changes to Git."""
    store = _profile_store(profile)
    try:
        commit_hash = commit_profile_store(store.profile_dir, message, init=init)
    except GitError as exc:
        raise typer.BadParameter(str(exc)) from exc

    if not commit_hash:
        typer.echo("Nothing to commit")
        raise typer.Exit(0)
    typer.echo(f"Committed {commit_hash[:8]}")
