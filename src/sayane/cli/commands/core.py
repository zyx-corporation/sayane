"""Core top-level command registration."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Callable

import typer
import yaml

from sayane.adapters.factory import get_adapter
from sayane.bridge.auth import format_pairing_code, load_or_create_token
from sayane.bridge.config import BridgeConfig
from sayane.cli.i18n import t
from sayane.cli.paths import context_dir, default_profile_dir, default_profile_file
from sayane.core.builder import build_prompt_ir

LoadProfile = Callable[[Path | None], tuple[Path, object]]


def _status_line(label: str, present: bool) -> str:
    return f"{label}: {'set' if present else 'missing'}"


def _load_judge_settings(home: Path) -> dict[str, object]:
    judge_path = home / "judge.yaml"
    if not judge_path.is_file():
        return {}
    try:
        raw = yaml.safe_load(judge_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    if isinstance(raw, dict):
        return raw
    return {}


def register_core_commands(
    app: typer.Typer,
    load_profile_fn: LoadProfile,
    init_template: str,
) -> None:
    """Register core top-level commands on the given Typer app."""

    @app.command()
    def doctor(
        topic: Annotated[
            str | None,
            typer.Argument(help="Optional topic: judge"),
        ] = None,
    ) -> None:
        """Run local diagnostic checks for bridge and judge settings."""
        if topic not in (None, "judge"):
            raise typer.BadParameter("Supported topic: judge")

        config = BridgeConfig()
        judge_settings = _load_judge_settings(config.home)
        judge_base = os.environ.get("SAYANE_JUDGE_BASE_URL") or judge_settings.get("base_url")
        judge_key = os.environ.get("SAYANE_JUDGE_API_KEY") or judge_settings.get("api_key")
        judge_model = os.environ.get("SAYANE_JUDGE_MODEL") or judge_settings.get("model")
        openai_key = os.environ.get("OPENAI_API_KEY")

        if topic is None:
            typer.echo(_status_line("Bridge token", config.token_file.is_file()))
            typer.echo(_status_line("Profile store", default_profile_file().is_file()))
        typer.echo(_status_line("Judge base URL", bool(judge_base)))
        typer.echo(_status_line("Judge API key", bool(judge_key)))
        typer.echo(_status_line("Judge model", bool(judge_model)))
        typer.echo(_status_line("OpenAI API key", bool(openai_key)))

        if openai_key and not judge_key:
            typer.echo(
                (
                    "warning: OPENAI_API_KEY is set but SAYANE_JUDGE_API_KEY is "
                    "missing. Sayane judge uses SAYANE_JUDGE_API_KEY."
                ),
                err=True,
            )

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
        profile_file.write_text(init_template.format(now=now), encoding="utf-8")
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
        path, loaded = load_profile_fn(profile)
        from sayane.core.profile_quality import validate_profile_quality

        for warning in validate_profile_quality(loaded):
            typer.echo(f"warning: {warning}", err=True)
        ir = build_prompt_ir(loaded, instruction=instruction, profile_root=path.parent)
        compiled = get_adapter(target).compile(ir)
        typer.echo(json.dumps(compiled.payload, ensure_ascii=False, indent=2))

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

        from sayane.core.build_info import format_build_info_startup_line, get_build_info

        build = get_build_info()
        token, created = load_or_create_token(config)
        typer.echo(t("serve.listening", host=host, port=port))
        typer.echo(format_build_info_startup_line(build))
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
