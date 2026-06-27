"""Storage command group registration."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from sayane.cli.i18n import t
from sayane.cli.runtime_config import CliVaultMode, resolve_cli_bridge_config
from sayane.vault.unlock_policy import UnlockLevel


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
        ExternalTargetPathError,
        export_to_vault,
        import_from_vault,
        iter_vault_markdown,
        resolve_obsidian_vault,
    )
    from sayane.core.audit_trail import get_audit_store
    from sayane.core.export_package import (
        build_vault_aware_package,
        locate_package_artifact,
        preview_package,
        render_preview_text,
        verify_package,
    )
    from sayane.core.import_bundle import (
        ImportMetadata,
        create_import_candidates,
        import_bundle_with_semantic_review,
        parse_bundle,
    )
    from sayane.storage.candidates import save_candidate

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

    def _parse_scopes(scope: str | None) -> list[str] | None:
        if scope is None:
            return None
        scopes = [item.strip() for item in scope.split(",") if item.strip()]
        return scopes or None

    def _require_legacy_external(action: str, *, confirmed: bool) -> None:
        if confirmed:
            return
        raise typer.BadParameter(t("error.storage_legacy_external_confirmation", action=action))

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
        source_subdir: Annotated[
            str | None,
            typer.Option("--source-subdir", help="Bounded subdirectory under the external vault root."),
        ] = None,
        legacy_compatible: Annotated[
            bool,
            typer.Option("--legacy-compatible", help="Confirm use of legacy external integration path."),
        ] = False,
    ) -> None:
        """Import markdown from an Obsidian vault."""
        vault_path = _vault_path(vault)
        bundle = _open_store(profile)
        if dry_run:
            try:
                paths = iter_vault_markdown(vault_path, subdir=source_subdir)
            except ExternalTargetPathError as exc:
                raise typer.BadParameter(str(exc)) from exc
            for p in paths:
                typer.echo(
                    p.relative_to(
                        vault_path.resolve()
                        if source_subdir is None
                        else (vault_path.resolve() / source_subdir)
                    ).as_posix()
                )
            typer.echo(t("storage.would_import", count=len(paths)))
            return
        _require_legacy_external("import", confirmed=legacy_compatible)
        try:
            imported = import_from_vault(
                vault_path,
                bundle.context.context_dir,
                subdir=source_subdir,
            )
        except ExternalTargetPathError as exc:
            raise typer.BadParameter(str(exc)) from exc
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
        legacy_compatible: Annotated[
            bool,
            typer.Option("--legacy-compatible", help="Confirm use of legacy external integration path."),
        ] = False,
    ) -> None:
        """Export context markdown into vault/<subdir>/."""
        _require_legacy_external("export", confirmed=legacy_compatible)
        vault_path = _vault_path(vault)
        bundle = _open_store(profile)
        try:
            exported = export_to_vault(bundle.context.context_dir, vault_path, subdir=subdir)
        except ExternalTargetPathError as exc:
            raise typer.BadParameter(str(exc)) from exc
        typer.echo(t("storage.exported", count=len(exported), path=vault_path / subdir))

    @storage_app.command("export-package")
    def storage_export_package(
        output: Annotated[
            Path,
            typer.Option("--output", "-o", help="Output directory for the vault-aware package."),
        ] = Path("./sayane-external-package"),
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        scope: Annotated[
            str | None,
            typer.Option("--scope", help="Comma-separated scopes for exported bundle sections."),
        ] = None,
        include_audit: Annotated[
            bool,
            typer.Option("--include-audit/--no-include-audit", help="Include redacted audit export."),
        ] = True,
        sign: Annotated[
            bool,
            typer.Option("--sign", help="Sign the package manifest when signing keys are configured."),
        ] = False,
    ) -> None:
        """Export one vault-aware external review package."""
        bundle = _open_store(profile)
        manifest = build_vault_aware_package(
            output,
            profile=bundle.profile.load(),
            profile_id=bundle.profile_id,
            scopes=_parse_scopes(scope),
            audit_store=get_audit_store(),
            include_audit=include_audit,
            sign=sign,
        )
        typer.echo(t("storage.package_exported", path=output))
        typer.echo(t("storage.package_id", package_id=manifest.get("package_id", "unknown")))
        typer.echo(t("storage.package_artifacts", count=manifest.get("summary", {}).get("artifact_count", 0)))

    @storage_app.command("import-package")
    def storage_import_package(
        package_dir: Annotated[Path, typer.Argument(help="Vault-aware external package directory.")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Preview reviewable candidates from a vault-aware external package."""
        result = verify_package(package_dir)
        if result["status"] == "FAILED":
            typer.echo(render_preview_text(preview_package(package_dir)))
            raise typer.BadParameter(t("error.storage_package_verification_failed"))

        bundle_path = locate_package_artifact(package_dir, "context_bundle")
        if bundle_path is None or not bundle_path.exists():
            raise typer.BadParameter(t("error.storage_package_bundle_missing"))

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(t("error.storage_package_bundle_invalid"))

        store = _open_store(profile)
        candidates, review = import_bundle_with_semantic_review(parsed, store.profile.load())

        typer.echo(render_preview_text(preview_package(package_dir)))
        if not candidates:
            typer.echo(t("import.no_candidates"))
            typer.echo(t("storage.package_preview_only"))
            return

        typer.echo("")
        typer.echo(t("import.candidates_header", count=len(candidates)))
        for index, candidate in enumerate(candidates):
            typer.echo(f"\n--- Candidate {index + 1} ---")
            typer.echo(f"  Section: {candidate['section']}")
            typer.echo(f"  Action:  {candidate['action']}")
            if candidate["current_value"]:
                typer.echo(f"  Current: {candidate['current_value']!r}"[:140])
            typer.echo(f"  Proposed: {candidate['proposed_value']!r}"[:140])
            flags = review["candidate_flags"][index] if index < len(review["candidate_flags"]) else []
            if flags:
                typer.echo("  Flags:")
                for flag in flags:
                    typer.echo(f"    - {flag}")
            warnings = review["candidate_warnings"][index] if index < len(review["candidate_warnings"]) else []
            if warnings:
                typer.echo("  Warnings:")
                for warning in warnings:
                    typer.echo(f"    - {warning['message']}")

        typer.echo("")
        typer.echo(t("storage.package_preview_only"))

    @storage_app.command("queue-package")
    def storage_queue_package(
        package_dir: Annotated[Path, typer.Argument(help="Vault-aware external package directory.")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        vault_mode: Annotated[
            CliVaultMode | None,
            typer.Option("--vault-mode", help="Explicit Local Vault mode: test | development | macos-keychain."),
        ] = None,
        vault_sqlite: Annotated[
            str | None,
            typer.Option("--vault-sqlite", help="Explicit Local Vault SQLite path."),
        ] = None,
        unlock_level: Annotated[
            UnlockLevel | None,
            typer.Option("--unlock-level", help="Unlock level when using --vault-mode."),
        ] = None,
    ) -> None:
        """Queue one verified package into the reviewable candidate store."""
        preview = preview_package(package_dir)
        result = verify_package(package_dir)
        if result["status"] == "FAILED":
            typer.echo(render_preview_text(preview))
            raise typer.BadParameter(t("error.storage_package_verification_failed"))

        manifest = result.get("manifest") or {}
        boundary = manifest.get("boundary", {})
        if boundary.get("import_contract") != "preview_only":
            raise typer.BadParameter(t("error.storage_package_queue_contract"))
        if boundary.get("reserved_future_mutating_workflow") != "separate_explicit_review_queue_import":
            raise typer.BadParameter(t("error.storage_package_queue_contract"))

        bundle_path = locate_package_artifact(package_dir, "context_bundle")
        if bundle_path is None or not bundle_path.exists():
            raise typer.BadParameter(t("error.storage_package_bundle_missing"))

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(t("error.storage_package_bundle_invalid"))

        store = _open_store(profile)
        draft_candidates = create_import_candidates(
            parsed,
            store.profile.load(),
            import_meta=ImportMetadata(
                import_id=manifest.get("package_id", "package-import"),
                source_path=str(bundle_path),
                source_format="yaml",
                source_target=manifest.get("package_kind"),
            ),
            target_profile_id=store.profile_id,
        )

        sqlite_path = Path(vault_sqlite) if vault_sqlite else None
        candidate_cfg = resolve_cli_bridge_config(
            vault_mode=vault_mode,
            vault_sqlite=sqlite_path,
            unlock_level=unlock_level,
            unlock_purpose="cli-storage-queue-package",
            profile_id=store.profile_id,
        )

        persisted_ids: list[str] = []
        for candidate in draft_candidates:
            save_candidate(candidate_cfg, candidate)
            persisted_ids.append(candidate.id)

        typer.echo(render_preview_text(preview))
        typer.echo("")
        typer.echo(t("storage.package_queued", count=len(persisted_ids)))
        for candidate_id in persisted_ids:
            typer.echo(t("storage.package_candidate_id", candidate_id=candidate_id))

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
        legacy_compatible: Annotated[
            bool,
            typer.Option("--legacy-compatible", help="Confirm use of legacy external integration path."),
        ] = False,
    ) -> None:
        """Commit profile and context to Git."""
        _require_legacy_external("commit", confirmed=legacy_compatible)
        bundle = _open_store(profile)
        if bundle.backend != "filesystem":
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
