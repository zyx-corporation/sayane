"""Build Sayane Typer application (locale-aware)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml

import sayane
from sayane.adapters.factory import get_adapter
from sayane.bridge.auth import format_pairing_code, load_or_create_token
from sayane.bridge.config import BridgeConfig
from sayane.cli.help_cmd import register_help
from sayane.cli.i18n import t
from sayane.cli.paths import (
    context_dir,
    default_profile_dir,
    default_profile_file,
    resolve_profile_path,
)
from sayane.core.builder import build_prompt_ir
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


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"sayane {sayane.__version__}")
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

    _register_profile(app)
    _register_core_commands(app)
    register_help(app)
    _register_candidate(app)
    _register_storage(app)
    _register_mcp(app)
    from sayane.cli.plugins import register_cli_extensions

    register_cli_extensions(app)
    return app


def _load(profile: Path | None) -> tuple[Path, object]:
    path = resolve_profile_path(profile)
    if not path.exists():
        raise typer.BadParameter(t("error.profile_not_found", path=path))
    return path, load_profile(path)


def _register_profile(app: typer.Typer) -> None:
    profile_app = typer.Typer(help=t("group.profile"), no_args_is_help=True)

    @profile_app.command("inspect")
    def profile_inspect(
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Show a summary of the loaded profile."""
        path, loaded = _load(profile)
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
        _path, loaded = _load(profile)
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


def _register_core_commands(app: typer.Typer) -> None:
    @app.command()
    def init(
        force: Annotated[bool, typer.Option("--force")] = False,
    ) -> None:
        """Initialize the local Sayane profile store."""
        profile_dir = default_profile_dir()
        profile_file = default_profile_file()
        ctx = context_dir()

        if profile_file.exists() and not force:
            typer.echo(t("init.exists", path=profile_dir))
            raise typer.Exit(0)

        now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        profile_dir.mkdir(parents=True, exist_ok=True)
        ctx.mkdir(parents=True, exist_ok=True)
        profile_file.write_text(INIT_TEMPLATE.format(now=now), encoding="utf-8")
        (ctx / "MyContext.md").write_text("# My Context\n", encoding="utf-8")
        (ctx / "AI_HANDOFF.md").write_text("# AI Handoff\n", encoding="utf-8")
        from sayane.storage.git_integration import auto_commit_profile_store

        commit_hash = auto_commit_profile_store(profile_dir, "sayane: initial profile")
        typer.echo(t("init.done", path=profile_dir))
        if commit_hash:
            typer.echo(t("storage.committed", hash=commit_hash[:8]))

    @app.command()
    def compile(
        target: Annotated[str, typer.Option("--target")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
    ) -> None:
        """Build Prompt IR and compile to the target LLM format."""
        path, loaded = _load(profile)
        from sayane.core.profile_quality import validate_profile_quality

        for warning in validate_profile_quality(loaded):
            typer.echo(f"warning: {warning}", err=True)
        ir = build_prompt_ir(loaded, instruction=instruction, profile_root=path.parent)
        compiled = get_adapter(target).compile(ir)
        typer.echo(json.dumps(compiled.payload, ensure_ascii=False, indent=2))

    @app.command()
    def export(
        format: Annotated[str, typer.Option("--format")],
        target: Annotated[str, typer.Option("--target")] = "chatgpt",
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
    ) -> None:
        """Export compiled prompt as markdown."""
        if format != "markdown":
            raise typer.BadParameter(t("error.unsupported_format", format=format))

        path, loaded = _load(profile)
        ir = build_prompt_ir(loaded, instruction=instruction, profile_root=path.parent)
        compiled = get_adapter(target).compile(ir)

        typer.echo(t("export.title") + "\n")
        typer.echo(t("export.target", target=compiled.target))
        typer.echo(t("export.format", format=compiled.format) + "\n")
        typer.echo(t("export.prompt_ir") + "\n")
        typer.echo("```yaml")
        typer.echo(yaml.safe_dump(ir.model_dump(mode="json"), allow_unicode=True, sort_keys=False))
        typer.echo("```\n")
        typer.echo(t("export.compiled") + "\n")
        typer.echo("```json")
        typer.echo(json.dumps(compiled.payload, ensure_ascii=False, indent=2))
        typer.echo("```")

    @app.command()
    def serve(
        host: Annotated[str, typer.Option("--host")] = "127.0.0.1",
        port: Annotated[int, typer.Option("--port")] = 38741,
    ) -> None:
        """Start the Local Bridge API server."""
        import uvicorn

        if host not in ("127.0.0.1", "localhost", "::1"):
            raise typer.BadParameter(t("error.bridge_localhost"))

        config = BridgeConfig(host=host, port=port)
        from sayane.storage.base import StorageBackendError
        from sayane.storage.config import load_storage_config
        from sayane.storage.registry import get_backend_factory

        storage_cfg = load_storage_config(config.home)
        try:
            get_backend_factory(storage_cfg.backend)
        except StorageBackendError as exc:
            typer.echo(str(exc), err=True)
            if storage_cfg.backend == "encrypted-sqlite":
                typer.echo(
                    "Install sayane-pro, or run:\n  sayane storage backend set filesystem",
                    err=True,
                )
            raise typer.Exit(1) from exc

        token, created = load_or_create_token(config)
        typer.echo(t("serve.listening", host=host, port=port))
        typer.echo(t("serve.token_file", path=config.token_file))
        if created:
            typer.echo(t("serve.pairing", code=format_pairing_code(token)))
            typer.echo(t("serve.auth_hint"))

        uvicorn.run(
            "sayane.bridge.app:create_app",
            factory=True,
            host=host,
            port=port,
            log_level="info",
        )


def _register_candidate(app: typer.Typer) -> None:
    from sayane.evaluators.service import (
        approve_candidate,
        diff_candidate,
        evaluate_candidate,
        reject_candidate,
    )
    from sayane.storage.candidates import list_candidate_ids, load_candidate
    from sayane.storage.lineage_store import list_records

    candidate_app = typer.Typer(help=t("group.candidate"), no_args_is_help=True)

    def _config() -> BridgeConfig:
        return BridgeConfig()

    @candidate_app.command("list")
    def candidate_list() -> None:
        """List candidate update ids."""
        ids = list_candidate_ids(_config())
        if not ids:
            typer.echo(t("candidate.none"))
            raise typer.Exit(0)
        for cid in ids:
            try:
                c = load_candidate(_config(), cid)
                rde = c.evaluation.rde_class if c.evaluation else "-"
                typer.echo(f"{cid}\t{c.status}\t{rde}")
            except Exception:
                typer.echo(f"{cid}\t?")

    @candidate_app.command("show")
    def candidate_show(candidate_id: Annotated[str, typer.Argument()]) -> None:
        """Show full candidate record."""
        candidate = load_candidate(_config(), candidate_id)
        typer.echo(yaml.safe_dump(candidate.model_dump(mode="json"), allow_unicode=True))

    @candidate_app.command("evaluate")
    def candidate_evaluate(
        candidate_id: Annotated[str, typer.Argument()],
        level: Annotated[int, typer.Option("--level", min=0, max=3)] = 1,
    ) -> None:
        """Run RDE + UIB evaluation."""
        if level == 0:
            typer.echo(t("candidate.level0"))
            raise typer.Exit(0)
        candidate = evaluate_candidate(_config(), candidate_id, level=level)
        typer.echo(yaml.safe_dump(candidate.evaluation.model_dump(mode="json"), allow_unicode=True))

    @candidate_app.command("approve")
    def candidate_approve(
        candidate_id: Annotated[str, typer.Argument()],
        force_critical: Annotated[bool, typer.Option("--force-critical")] = False,
    ) -> None:
        """Approve and merge into profile."""
        try:
            candidate = approve_candidate(
                _config(),
                candidate_id,
                force_critical=force_critical,
            )
            typer.echo(
                t(
                    "candidate.approved",
                    id=candidate.id,
                    profile_id=candidate.target_profile_id,
                ),
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @candidate_app.command("reject")
    def candidate_reject(
        candidate_id: Annotated[str, typer.Argument()],
        reason: Annotated[str | None, typer.Option("--reason")] = None,
    ) -> None:
        """Reject candidate without merging."""
        candidate = reject_candidate(_config(), candidate_id, reason=reason)
        typer.echo(t("candidate.rejected", id=candidate.id))

    @candidate_app.command("diff")
    def candidate_diff(candidate_id: Annotated[str, typer.Argument()]) -> None:
        """Show rule-based diff vs current profile."""
        result = diff_candidate(_config(), candidate_id)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

    @candidate_app.command("lineage")
    def candidate_lineage(
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        limit: Annotated[int, typer.Option("--limit")] = 20,
    ) -> None:
        """Show recent lineage records for a profile."""
        records = list_records(_config(), profile_id, limit=limit)
        if not records:
            typer.echo(t("candidate.lineage_none"))
            raise typer.Exit(0)
        for rec in records:
            typer.echo(json.dumps(rec, ensure_ascii=False))

    app.add_typer(candidate_app, name="candidate")


def _register_storage(app: typer.Typer) -> None:
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


def _register_mcp(app: typer.Typer) -> None:
    from sayane.mcp.operations import get_operations

    mcp_app = typer.Typer(help=t("group.mcp"), no_args_is_help=True)

    def _echo_json(data: object) -> None:
        typer.echo(json.dumps(data, ensure_ascii=False, indent=2))

    @mcp_app.command("serve")
    def mcp_serve() -> None:
        """Start MCP server on stdio."""
        from sayane.mcp.server import run_stdio

        typer.echo(t("mcp.starting"), err=True)
        run_stdio()

    @mcp_app.command("list-profiles")
    def mcp_list_profiles() -> None:
        _echo_json(get_operations().list_profiles())

    @mcp_app.command("inspect-profile")
    def mcp_inspect_profile(
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
    ) -> None:
        try:
            _echo_json(get_operations().inspect_profile(profile_id=profile_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("compile")
    def mcp_compile(
        target: Annotated[str, typer.Option("--target")],
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
    ) -> None:
        try:
            _echo_json(
                get_operations().compile_prompt(
                    target=target,
                    profile_id=profile_id,
                    instruction=instruction,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("context-packet")
    def mcp_context_packet(
        target: Annotated[str, typer.Option("--target")],
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        instruction: Annotated[str | None, typer.Option("--instruction")] = None,
    ) -> None:
        try:
            _echo_json(
                get_operations().generate_context_packet(
                    target=target,
                    profile_id=profile_id,
                    instruction=instruction,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("list-candidates")
    def mcp_list_candidates() -> None:
        _echo_json(get_operations().list_candidate_updates())

    @mcp_app.command("show-candidate")
    def mcp_show_candidate(candidate_id: Annotated[str, typer.Argument()]) -> None:
        try:
            _echo_json(get_operations().show_candidate(candidate_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("evaluate-candidate")
    def mcp_evaluate_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        level: Annotated[int, typer.Option("--level", min=1, max=3)] = 1,
    ) -> None:
        try:
            _echo_json(get_operations().evaluate_candidate(candidate_id, level=level))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("approve-candidate")
    def mcp_approve_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        force_critical: Annotated[bool, typer.Option("--force-critical")] = False,
    ) -> None:
        try:
            _echo_json(
                get_operations().approve_candidate(
                    candidate_id,
                    force_critical=force_critical,
                ),
            )
        except (FileNotFoundError, ValueError) as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("reject-candidate")
    def mcp_reject_candidate(
        candidate_id: Annotated[str, typer.Argument()],
        reason: Annotated[str | None, typer.Option("--reason")] = None,
    ) -> None:
        try:
            _echo_json(get_operations().reject_candidate(candidate_id, reason=reason))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    @mcp_app.command("diff-candidate")
    def mcp_diff_candidate(candidate_id: Annotated[str, typer.Argument()]) -> None:
        try:
            _echo_json(get_operations().diff_candidate(candidate_id))
        except FileNotFoundError as exc:
            raise typer.BadParameter(str(exc)) from exc

    app.add_typer(mcp_app, name="mcp")
