"""Omomuki CLI — Phase 1 MVP."""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import typer
import yaml

from omomuki.adapters.factory import get_adapter
from omomuki.bridge.auth import format_pairing_code, load_or_create_token
from omomuki.bridge.config import BridgeConfig
from omomuki.cli.candidate_cli import candidate_app
from omomuki.cli.mcp_cli import mcp_app
from omomuki.cli.paths import (
    context_dir,
    default_profile_dir,
    default_profile_file,
    resolve_profile_path,
)
from omomuki.core.builder import build_prompt_ir
from omomuki.core.loader import load_profile

app = typer.Typer(no_args_is_help=True, help="Omomuki — persona and context portability for LLMs.")
profile_app = typer.Typer(help="Profile operations.")
app.add_typer(profile_app, name="profile")
app.add_typer(mcp_app, name="mcp")
app.add_typer(candidate_app, name="candidate")

INIT_TEMPLATE = """\
version: "0.1.0"
kind: "OmomukiProfile"
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


def _load(profile: Path | None) -> tuple[Path, object]:
    path = resolve_profile_path(profile)
    if not path.exists():
        raise typer.BadParameter(f"Profile not found: {path}. Run `omomuki init` first.")
    return path, load_profile(path)


@app.command()
def init(
    force: Annotated[
        bool,
        typer.Option("--force", help="Overwrite existing profile store."),
    ] = False,
) -> None:
    """Initialize the local Omomuki profile store."""
    profile_dir = default_profile_dir()
    profile_file = default_profile_file()
    ctx_dir = context_dir()

    if profile_file.exists() and not force:
        typer.echo(f"Profile store already exists: {profile_dir}")
        raise typer.Exit(0)

    now = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    profile_dir.mkdir(parents=True, exist_ok=True)
    ctx_dir.mkdir(parents=True, exist_ok=True)
    profile_file.write_text(INIT_TEMPLATE.format(now=now), encoding="utf-8")
    (ctx_dir / "MyContext.md").write_text("# My Context\n", encoding="utf-8")
    (ctx_dir / "AI_HANDOFF.md").write_text("# AI Handoff\n", encoding="utf-8")
    typer.echo(f"Initialized profile store at {profile_dir}")


@profile_app.command("inspect")
def profile_inspect(
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
) -> None:
    """Show a summary of the loaded profile."""
    path, loaded = _load(profile)
    p = loaded
    typer.echo(f"Path: {path}")
    typer.echo(f"Kind: {p.kind} (v{p.version})")
    typer.echo(f"Identity: {p.identity.name} ({p.identity.preferred_name or '-'})")
    if p.identity.roles:
        typer.echo(f"Roles: {', '.join(p.identity.roles)}")
    if p.voice.tone:
        typer.echo(f"Tone: {', '.join(p.voice.tone)}")
    if p.values.core:
        typer.echo(f"Values: {', '.join(p.values.core)}")
    if p.knowledge and p.knowledge.concepts:
        typer.echo(f"Concepts: {', '.join(p.knowledge.concepts)}")
    if p.context_index.entrypoint:
        typer.echo(f"Context entrypoint: {p.context_index.entrypoint}")


@profile_app.command("diff")
def profile_diff(
    candidate_id: Annotated[
        str,
        typer.Option("--candidate", help="Candidate id to diff against profile"),
    ],
) -> None:
    """Show profile diff for a candidate (alias for omomuki candidate diff)."""
    from omomuki.evaluators.service import diff_candidate

    diff = diff_candidate(BridgeConfig(), candidate_id)
    typer.echo(json.dumps(diff, ensure_ascii=False, indent=2))


@app.command()
def compile(
    target: Annotated[str, typer.Option("--target", help="chatgpt or claude")],
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
    instruction: Annotated[
        str | None,
        typer.Option("--instruction", help="Task instruction for Prompt IR"),
    ] = None,
) -> None:
    """Build Prompt IR and compile to the target LLM format."""
    _, loaded = _load(profile)
    ir = build_prompt_ir(loaded, instruction=instruction)
    compiled = get_adapter(target).compile(ir)
    typer.echo(json.dumps(compiled.payload, ensure_ascii=False, indent=2))


@app.command()
def export(
    format: Annotated[
        str,
        typer.Option("--format", help="Export format (markdown)"),
    ],
    target: Annotated[
        str,
        typer.Option("--target", help="chatgpt or claude"),
    ] = "chatgpt",
    profile: Annotated[
        Path | None,
        typer.Option("--profile", help="Path to omomuki.profile.yaml"),
    ] = None,
    instruction: Annotated[
        str | None,
        typer.Option("--instruction", help="Task instruction for Prompt IR"),
    ] = None,
) -> None:
    """Export compiled prompt as markdown."""
    if format != "markdown":
        raise typer.BadParameter(f"Unsupported format: {format}")

    _, loaded = _load(profile)
    ir = build_prompt_ir(loaded, instruction=instruction)
    compiled = get_adapter(target).compile(ir)

    typer.echo("# Omomuki Compiled Prompt\n")
    typer.echo(f"- Target: {compiled.target}")
    typer.echo(f"- Format: {compiled.format}\n")
    typer.echo("## Prompt IR\n")
    typer.echo("```yaml")
    typer.echo(yaml.safe_dump(ir.model_dump(mode="json"), allow_unicode=True, sort_keys=False))
    typer.echo("```\n")
    typer.echo("## Compiled Payload\n")
    typer.echo("```json")
    typer.echo(json.dumps(compiled.payload, ensure_ascii=False, indent=2))
    typer.echo("```")


@app.command()
def serve(
    host: Annotated[
        str,
        typer.Option("--host", help="Bind address (127.0.0.1 only in production)"),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option("--port", help="Listen port"),
    ] = 38741,
) -> None:
    """Start the Local Bridge API server."""
    import uvicorn

    if host not in ("127.0.0.1", "localhost", "::1"):
        raise typer.BadParameter("Bridge must bind to localhost only")

    config = BridgeConfig(host=host, port=port)
    token, created = load_or_create_token(config)
    typer.echo(f"Local Bridge listening on http://{host}:{port}")
    typer.echo(f"Bearer token file: {config.token_file}")
    if created:
        typer.echo(f"Pairing code: {format_pairing_code(token)}")
        typer.echo("Use Authorization: Bearer <token> for protected endpoints")

    uvicorn.run(
        "omomuki.bridge.app:create_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )


def main() -> None:
    app()


if __name__ == "__main__":
    main()
