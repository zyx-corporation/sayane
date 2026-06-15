"""Storage command group registration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sayane.cli.i18n import t


def register_storage(app: typer.Typer) -> None:
    """Register storage commands on the given Typer app."""
    from sayane.storage.base import StorageBackendError, StorageBundle
    from sayane.storage.context_index import apply_context_index
    from sayane.storage.factory import list_backends, open_storage, set_storage_backend
    from sayane.storage.git_integration import (
        GitError,
        auto_commit_profile_store,
        commit_profile_store,
    )
    from sayane.storage.obsidian import (
        export_to_vault,
        import_from_vault,
        iter_vault_markdown,
        resolve_obsidian_vault,
    )

    storage_app = typer.Typer(help=t("group.storage"), no_args_is_help=True)
    backend_app = typer.Typer(help=t("group.storage_backend"), no_args_is_help=True)

    def _open_store(profile: Path | None) -> StorageBundle:
        try:
            return open_storage(profile=profile)
        except StorageBackendError as exc:
            raise typer.BadParameter(str(exc)) from exc

    def _vault_path(vault: Path | None) -> Path:
        try:
            return resolve_obsidian_vault(vault)
        except FileNotFoundError as exc:
            raise typer.BadParameter(t("error.obsidian_vault_required")) from exc

    def _maybe_auto_commit(bundle: StorageBundle, message: str) -> None:
        if not bundle.uses_git_auto_commit:
            return
        commit_hash = auto_commit_profile_store(bundle.profile.profile_dir, message)
        if commit_hash:
            typer.echo(t("storage.committed", hash=commit_hash[:8]))

    @backend_app.command("status")
    def storage_backend_status() -> None:
        """Show active storage backend and profile id."""
        bundle = open_storage()
        typer.echo(t("storage.backend", backend=bundle.backend, profile_id=bundle.profile_id))
        typer.echo(t("storage.backend_profile_dir", path=bundle.profile.profile_dir))

    @backend_app.command("list")
    def storage_backend_list() -> None:
        """List registered storage backends."""
        for name in list_backends():
            typer.echo(name)

    @backend_app.command("set")
    def storage_backend_set(
        backend: Annotated[str, typer.Argument(help="Backend name (e.g. filesystem)")],
    ) -> None:
        """Select storage backend in ~/.sayane/config.yaml."""
        try:
            config = set_storage_backend(backend)
        except StorageBackendError as exc:
            raise typer.BadParameter(str(exc)) from exc
        typer.echo(t("storage.backend_set", backend=config.backend, profile_id=config.profile_id))

    storage_app.add_typer(backend_app, name="backend")

    @storage_app.command("import")
    def storage_import(
        vault: Annotated[
            Path | None,
            typer.Argument(help="Obsidian vault (default: $SAYANE_OBSIDIAN_VAULT)"),
        ] = None,
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        dry_run: Annotated[bool, typer.Option("--dry-run")] = False,
    ) -> None:
        """Import markdown from an Obsidian vault."""
        vault_path = _vault_path(vault)
        bundle = _open_store(profile)
        if dry_run:
            paths = iter_vault_markdown(vault_path)
            for p in paths:
                typer.echo(p.relative_to(vault_path.resolve()).as_posix())
            typer.echo(t("storage.would_import", count=len(paths)))
            return
        imported = import_from_vault(vault_path, bundle.context.context_dir)
        profile_obj = apply_context_index(bundle.profile.load(), bundle.profile.profile_dir)
        bundle.profile.save(profile_obj)
        typer.echo(t("storage.imported", count=len(imported), path=bundle.context.context_dir))
        typer.echo(t("storage.index_updated"))
        _maybe_auto_commit(bundle, "sayane: storage import")

    @storage_app.command("export")
    def storage_export(
        vault: Annotated[
            Path | None,
            typer.Argument(help="Obsidian vault (default: $SAYANE_OBSIDIAN_VAULT)"),
        ] = None,
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        subdir: Annotated[str, typer.Option("--subdir")] = "sayane",
    ) -> None:
        """Export context markdown into vault/<subdir>/."""
        vault_path = _vault_path(vault)
        bundle = _open_store(profile)
        exported = export_to_vault(bundle.context.context_dir, vault_path, subdir=subdir)
        typer.echo(t("storage.exported", count=len(exported), path=vault_path / subdir))

    @storage_app.command("index")
    def storage_index(
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Regenerate context_index from context/."""
        bundle = _open_store(profile)
        profile_obj = apply_context_index(bundle.profile.load(), bundle.profile.profile_dir)
        bundle.profile.save(profile_obj)
        idx = profile_obj.context_index
        typer.echo(t("storage.entrypoint", path=idx.entrypoint))
        typer.echo(t("storage.handoff", path=idx.handoff))
        typer.echo(t("storage.entries", count=len(idx.entries)))
        _maybe_auto_commit(bundle, "sayane: storage index")

    @storage_app.command("commit")
    def storage_commit(
        message: Annotated[str, typer.Option("-m", "--message")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        init: Annotated[bool, typer.Option("--init")] = False,
    ) -> None:
        """Commit profile and context to Git."""
        bundle = _open_store(profile)
        if not bundle.uses_git_auto_commit:
            raise typer.BadParameter(t("error.storage_git_filesystem_only"))
        try:
            commit_hash = commit_profile_store(bundle.profile.profile_dir, message, init=init)
        except GitError as exc:
            raise typer.BadParameter(str(exc)) from exc
        if not commit_hash:
            typer.echo(t("storage.nothing_to_commit"))
            raise typer.Exit(0)
        typer.echo(t("storage.committed", hash=commit_hash[:8]))

    app.add_typer(storage_app, name="storage")
