"""Build Sayane Typer application (locale-aware)."""

from __future__ import annotations

import json
import os
import sys
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
    def capture(
        text: Annotated[str | None, typer.Option("--text", help="Capture body text.")] = None,
        file: Annotated[
            Path | None,
            typer.Option("--file", "-f", help="Read capture body from a file."),
        ] = None,
        source: Annotated[str | None, typer.Option("--source", help="Source label.")] = None,
        source_url: Annotated[str | None, typer.Option("--source-url")] = None,
        section: Annotated[
            str | None,
            typer.Option("--section", help="Target profile section (e.g. knowledge.concepts)."),
        ] = None,
        json_out: Annotated[bool, typer.Option("--json", help="Emit JSON response.")] = False,
    ) -> None:
        """Save captured text as a pending Candidate (same as Bridge POST /capture)."""
        from sayane.bridge.capture_store import save_capture
        from sayane.bridge.models import CaptureRequest

        if file is not None and text is not None:
            raise typer.BadParameter("Use either --text or --file, not both.")
        if file is not None:
            if not file.is_file():
                raise typer.BadParameter(f"File not found: {file}")
            content = file.read_text(encoding="utf-8")
        elif text is not None:
            content = text
        elif not sys.stdin.isatty():
            content = sys.stdin.read()
        else:
            typer.echo(
                "Provide capture content via --text, --file, or stdin pipe.",
                err=True,
            )
            raise typer.Exit(2)

        content = content.strip()
        if not content:
            raise typer.BadParameter("Capture content is empty.")

        try:
            response = save_capture(
                BridgeConfig(),
                CaptureRequest(
                    content=content,
                    source=source or "cli",
                    source_url=source_url,
                    section=section,
                ),
            )
        except ValueError as exc:
            raise typer.BadParameter(str(exc)) from exc

        if json_out:
            typer.echo(json.dumps(response.model_dump(), ensure_ascii=False, indent=2))
            return

        typer.echo(f"id: {response.id}")
        typer.echo(f"path: {response.path}")
        typer.echo(f"status: {response.status}")
        for warning in response.warnings:
            typer.echo(f"warning: {warning}", err=True)

    @app.command()
    def export(
        format: Annotated[str, typer.Option("--format")],
        target: Annotated[str, typer.Option("--target")] = "chatgpt",
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
        scope: Annotated[str | None, typer.Option("--scope", help="Comma-separated scopes: identity,interaction,technical,...")] = None,
    ) -> None:
        """Export profile context in yaml, markdown, or prompt format."""
        from sayane.core.export import export_markdown, export_prompt, export_yaml

        path, loaded = _load(profile)
        scopes = [s.strip() for s in scope.split(",") if s.strip()] if scope else ["identity", "interaction"]

        if format == "yaml":
            typer.echo(export_yaml(loaded, scopes))
        elif format == "markdown":
            typer.echo(export_markdown(loaded, scopes, target))
        elif format == "prompt":
            typer.echo(export_prompt(loaded, scopes, target))
        else:
            raise typer.BadParameter(t("error.unsupported_format", format=format))

    @app.command()
    def import_bundle(
        bundle: Annotated[Path, typer.Argument(help="Path to portable context bundle (yaml/md).")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Import a portable context bundle as reviewable Candidates (#143)."""
        from sayane.core.import_bundle import import_bundle_with_semantic_review, parse_bundle

        path, loaded = _load(profile)
        parsed = parse_bundle(bundle)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle}")

        # Bundle provenance verification (Phase 9)
        from sayane.core.bundle_provenance import verify_and_require_pass
        allowed, msg = verify_and_require_pass(parsed)
        typer.echo(f"Verification: {msg}")
        if not allowed:
            raise typer.BadParameter(f"Bundle verification failed. Import blocked.")

        candidates, review = import_bundle_with_semantic_review(parsed, loaded)
        if not candidates:
            typer.echo(t("import.no_candidates"))
            return
        typer.echo(t("import.candidates_header", count=len(candidates)))
        for i, c in enumerate(candidates):
            typer.echo(f"\n--- Candidate {i + 1} ---")
            typer.echo(f"  Section: {c['section']}")
            typer.echo(f"  Action:  {c['action']}")
            if c['current_value']:
                typer.echo(f"  Current: {json.dumps(c['current_value'], ensure_ascii=False)[:120]}")
            typer.echo(f"  Proposed: {json.dumps(c['proposed_value'], ensure_ascii=False)[:120]}")
            # Semantic review flags (Phase 6)
            flags = review["candidate_flags"][i] if i < len(review["candidate_flags"]) else []
            if flags:
                typer.echo(f"  Flags:")
                for flag in flags:
                    typer.echo(f"    - {flag}")
            warnings = review["candidate_warnings"][i] if i < len(review["candidate_warnings"]) else []
            if warnings:
                typer.echo(f"  Warnings:")
                for w in warnings:
                    typer.echo(f"    - {w['message']}")

        # Cross-candidate overlap warnings
        overlaps = review.get("overlap_warnings", [])
        for ow in overlaps:
            typer.echo(f"\n--- Overlap Warning ---")
            typer.echo(f"  Terms:")
            for term in ow.get("terms", []):
                typer.echo(f"    - {term}")
            typer.echo(f"  Candidates: {', '.join(str(i + 1) for i in ow.get('candidate_indices', []))}")
            typer.echo(f"  Note: {ow.get('note', '')}")

    @app.command()
    def review(
        action: Annotated[str, typer.Argument(help="list | show | diff | overlap | approve | reject | modify | defer | scoped-accept")],
        candidate_id: Annotated[str | None, typer.Argument()] = None,
        reason: Annotated[str | None, typer.Option("--reason", help="Reason for decision.")] = None,
        value: Annotated[str | None, typer.Option("--value", help="Applied value for modify (JSON).")] = None,
        scope: Annotated[str | None, typer.Option("--scope", help="Accepted scope: level:target:subscope.")] = None,
        conditions: Annotated[str | None, typer.Option("--conditions", help="Comma-separated conditions.")] = None,
        negative: Annotated[str | None, typer.Option("--negative", help="Comma-separated negative constraints.")] = None,
        filter_flag: Annotated[str | None, typer.Option("--filter", help="Filter: review_required | semantic_overlap | boundary_sensitive.")] = None,
    ) -> None:
        """Review import candidates (Phase 7/12)."""
        import json as _json
        from sayane.core.review_decision import (
            ReviewDecision,
            list_decisions,
            save_decision,
            validate_decision,
        )

        if action == "list":
            decisions = list_decisions()
            if not decisions:
                typer.echo("No review decisions recorded.")
                return
            filtered = decisions
            if filter_flag:
                filtered = [d for d in decisions if filter_flag in (d.review_flags or [])]
            typer.echo(f"{len(filtered)} review decision(s):")
            for d in filtered:
                applied = f" → {_json.dumps(d.applied_value, ensure_ascii=False)[:80]}" if d.applied_value else ""
                flags = f" [{', '.join(d.review_flags)}]" if d.review_flags else ""
                typer.echo(f"  [{d.decision.upper()}] {d.candidate_id} ({d.original_section}) — {d.reason[:60]}{applied}{flags}")
            return

        if action == "show":
            if not candidate_id:
                raise typer.BadParameter("candidate_id required for show")
            # Phase 12: provenance-aware detail view
            decisions = [d for d in list_decisions() if d.candidate_id == candidate_id]
            d = decisions[-1] if decisions else None
            typer.echo(f"=== Candidate Detail: {candidate_id} ===")
            if d:
                typer.echo(f"  Section: {d.original_section}")
                typer.echo(f"  Action:  {d.original_action}")
                typer.echo(f"  Decision: {d.decision.upper()}")
                if d.review_flags:
                    typer.echo(f"  Flags:   {', '.join(d.review_flags)}")
                if d.review_warnings:
                    typer.echo(f"  Warnings:")
                    for w in d.review_warnings:
                        typer.echo(f"    - {w.get('message', w)}")
                if d.transfer_path:
                    typer.echo(f"  Transfer path: {' → '.join(d.transfer_path)}")
                typer.echo(f"  Reason:  {d.reason or 'N/A'}")
                if d.applied_value:
                    typer.echo(f"  Applied: {_json.dumps(d.applied_value, ensure_ascii=False)[:120]}")
                # F-1.5/F-3: scoped accept metadata
                if d.decision == "scoped_accept":
                    if d.accepted_scope:
                        typer.echo(f"  Scope:   {d.accepted_scope.get('level', '?')}:{d.accepted_scope.get('target', '?')}:{d.accepted_scope.get('sub_scope', '?')}")
                    if d.conditions:
                        typer.echo(f"  Conditions:")
                        for c in d.conditions:
                            typer.echo(f"    - {c}")
                    if d.negative_constraints:
                        typer.echo(f"  Must NOT:")
                        for nc in d.negative_constraints:
                            typer.echo(f"    - {nc}")
                    pp = d.promotion_policy or {}
                    if pp.get("can_promote") is False:
                        typer.echo(f"  Promotion: blocked (requires review)")
                typer.echo(f"  Lineage: {d.lineage_event_id[:12]}")
            else:
                typer.echo("  No decisions recorded. Import a bundle first, then use review approve/reject/modify/defer.")
            return

        if action == "overlap":
            from sayane.core.review_decision import get_overlap_resolution
            if candidate_id:
                res = get_overlap_resolution(candidate_id)
                if res:
                    typer.echo(f"Overlap Group: {res.overlap_id}")
                    typer.echo(f"  Terms: {', '.join(res.terms)}")
                    typer.echo(f"  Candidates: {', '.join(res.candidate_ids)}")
                    typer.echo(f"  Resolved: {res.resolved}")
                    if res.resolution_reason:
                        typer.echo(f"  Reason: {res.resolution_reason}")
                else:
                    typer.echo("Overlap group not found.")
            else:
                typer.echo("Usage: sayane review overlap <overlap-id>")
            return

        if action == "diff":
            if not candidate_id:
                raise typer.BadParameter("candidate_id required for diff")
            from sayane.core.decision_diff import build_decision_diff, render_diff
            decisions = [d for d in list_decisions() if d.candidate_id == candidate_id]
            if not decisions:
                typer.echo("No decisions recorded. Import and review a candidate first.")
                return
            d = decisions[-1]
            diff = build_decision_diff(
                candidate_id=d.candidate_id,
                decision=d.decision,
                section=d.original_section,
                original_candidate=d.original_proposed,
                applied_value=d.applied_value,
                reason=d.reason,
                warnings_in=d.review_warnings,
            )
            typer.echo(render_diff(diff))
            return

        if not candidate_id:
            raise typer.BadParameter("candidate_id required for approve/reject/modify/defer/scoped-accept")

        if action == "scoped-accept":
            scope_parts = (scope or "").split(":")
            accepted_scope = {
                "level": scope_parts[0] if len(scope_parts) > 0 else "project",
                "target": scope_parts[1] if len(scope_parts) > 1 else None,
                "sub_scope": scope_parts[2] if len(scope_parts) > 2 else None,
            }
            cond_list = [c.strip() for c in (conditions or "").split(",") if c.strip()]
            neg_list = [n.strip() for n in (negative or "").split(",") if n.strip()]
            decision = ReviewDecision(
                candidate_id=candidate_id,
                decision="scoped_accept",
                reason=reason or "",
                accepted_scope=accepted_scope,
                conditions=cond_list,
                negative_constraints=neg_list,
                promotion_policy={"can_promote": False},
                reuse_policy={"review_on_reuse": True},
            )
            errors = validate_decision(decision, has_review_required=True)
            if errors:
                for e in errors:
                    typer.echo(f"Error: {e}", err=True)
                raise typer.Exit(1)
            save_decision("default", decision)
            typer.echo(f"Scoped accept: {candidate_id} → {accepted_scope}")
            return

        applied_value = None
        if value:
            try:
                applied_value = _json.loads(value)
            except _json.JSONDecodeError:
                raise typer.BadParameter(f"Invalid JSON for --value: {value}")

        decision = ReviewDecision(
            candidate_id=candidate_id,
            decision=action,  # type: ignore[arg-type]
            reason=reason or "",
            applied_value=applied_value,
            original_section="imported",
            original_action="add",
        )

        errors = validate_decision(decision, has_review_required=("review_required" in (reason or "")))
        if errors:
            for e in errors:
                typer.echo(f"Error: {e}", err=True)
            raise typer.Exit(1)

        save_decision("default", decision)
        typer.echo(f"Decision recorded: [{decision.decision.upper()}] {candidate_id} — lineage event: {decision.lineage_event_id[:12]}")

        # Append to audit trail (Phase 8)
        from sayane.core.audit_trail import build_audit_record, get_audit_store
        store = get_audit_store()
        audit = build_audit_record(decision, profile_updated=(action in ("approve", "modify")))
        store.append(audit)
        typer.echo(f"Audit: appended to {store.path}")

    @app.command()
    def context_compile(
        target: Annotated[str, typer.Option("--target", help="Target tool: cursor | claude-desktop")] = "cursor",
        mode: Annotated[str, typer.Option("--mode", help="Output mode: compact | full | strict")] = "full",
        show_scope: Annotated[bool, typer.Option("--show-scope")] = False,
    ) -> None:
        """Compile MCP context with scoped accept metadata (F-2)."""
        from sayane.core.review_decision import list_decisions
        from sayane.core.mcp_context import build_compiled_context, render_compiled_context_text

        scoped = [d for d in list_decisions() if d.decision == "scoped_accept"]
        compiled = build_compiled_context(target=target, mode=mode, scoped_decisions=scoped)

        if show_scope:
            typer.echo(render_compiled_context_text(compiled))
        else:
            typer.echo(json.dumps(compiled, ensure_ascii=False, indent=2))

    @app.command()
    def audit(
        action: Annotated[str, typer.Argument(help="list | by-candidate | by-term | unresolved | export")],
        query_value: Annotated[str | None, typer.Argument()] = None,
        format: Annotated[str | None, typer.Option("--format", help="Export format: markdown | json | jsonl")] = "markdown",
        output: Annotated[Path | None, typer.Option("--output", "-o", help="Output file.")] = None,
        candidate: Annotated[str | None, typer.Option("--candidate", help="Filter by candidate.")] = None,
        term: Annotated[str | None, typer.Option("--term", help="Filter by term.")] = None,
        decision: Annotated[str | None, typer.Option("--decision", help="Filter by decision.")] = None,
        redact: Annotated[bool, typer.Option("--redact")] = False,
    ) -> None:
        """Query the review decision audit trail (Phase 8)."""
        from sayane.core.audit_trail import get_audit_store
        store = get_audit_store()
        records = store.read_all()

        if action == "list":
            if not records:
                typer.echo("No audit records.")
                return
            typer.echo(f"{len(records)} audit record(s):")
            for r in records[-20:]:  # last 20
                d = r["decision"]
                c = r["candidate"]
                applied = f" → {json.dumps(r['result']['applied_value'], ensure_ascii=False)[:60]}" if r["result"]["applied_value"] else ""
                typer.echo(f"  [{d['type'].upper()}] {c['section']} — {d['reason'][:60]}{applied}")

        elif action == "by-candidate":
            if not query_value:
                raise typer.BadParameter("candidate_id required for by-candidate")
            matches = store.query(candidate_id=query_value)
            typer.echo(f"{len(matches)} record(s) for candidate {query_value}:")
            for r in matches:
                typer.echo(f"  [{r['decision']['type'].upper()}] {r['decision']['reason'][:80]}")

        elif action == "by-term":
            if not query_value:
                raise typer.BadParameter("term required for by-term")
            matches = store.query(term=query_value)
            typer.echo(f"{len(matches)} record(s) for term '{query_value}':")
            for r in matches:
                typer.echo(f"  [{r['decision']['type'].upper()}] {r['candidate']['section']} — flags={r['candidate'].get('flags', [])}")

        elif action == "export":
            from sayane.core.audit_export import build_export
            content = build_export(
                store,
                format=format or "markdown",
                candidate_id=candidate,
                term=term,
                decision=decision,
                redact=redact,
            )
            if output:
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(content, encoding="utf-8")
                typer.echo(f"Audit export written: {output}")
            else:
                typer.echo(content)

        else:
            raise typer.BadParameter(f"Unknown audit action: {action}")

    @app.command()
    def bundle_verify(
        bundle_path: Annotated[Path, typer.Argument(help="Path to context bundle.")],
    ) -> None:
        """Verify a context bundle's provenance and content hash (Phase 9)."""
        from sayane.core.import_bundle import parse_bundle
        from sayane.core.bundle_provenance import verify_bundle

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle_path}")

        result = verify_bundle(parsed)
        typer.echo(f"Bundle verification:")
        typer.echo(f"  Status: {result.status}")
        typer.echo(f"  Bundle ID: {result.bundle_id or 'N/A'}")
        if result.hash_value:
            typer.echo(f"  Hash: sha256:{result.hash_value}")
        typer.echo(f"  Signature: {result.signature_status}")
        if result.details:
            typer.echo(f"  Details: {result.details}")

    @app.command()
    def transfer_report(
        output: Annotated[Path, typer.Option("--output", "-o", help="Output file path.")] = Path("docs/transfer-tests/transfer-regression-report.md"),
        format: Annotated[str, typer.Option("--format", help="Output format: markdown | json")] = "markdown",
        fixtures_dir: Annotated[Path, typer.Option("--fixtures", help="Transfer fixtures directory.")] = Path("docs/transfer-tests"),
        audit_path: Annotated[Path | None, typer.Option("--audit", help="Audit store path.")] = None,
        fail_on_warnings: Annotated[bool, typer.Option("--fail-on-warnings")] = False,
    ) -> None:
        """Generate a cross-LLM transfer regression dashboard report (Phase 10)."""
        from sayane.core.audit_trail import AuditStore
        from sayane.core.transfer_report import generate_transfer_report, render_markdown_report

        audit_dir = audit_path.parent if audit_path else Path.home() / ".sayane" / "audit"
        audit_store = AuditStore(audit_dir) if audit_path else AuditStore(audit_dir)

        report = generate_transfer_report(
            transfer_dir=fixtures_dir,
            audit_store=audit_store,
            profile_path=Path("examples/profiles/minimal.yaml"),
        )

        if format == "json":
            import json as _json
            content = _json.dumps(report, ensure_ascii=False, indent=2)
        else:
            content = render_markdown_report(report)

        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content, encoding="utf-8")
        typer.echo(f"Report written: {output}")

        # Exit code
        status = report["status"]
        if status == "FAIL":
            raise typer.Exit(1)
        if fail_on_warnings and status == "PASS_WITH_WARNINGS":
            raise typer.Exit(1)

    @app.command()
    def policy(
        action: Annotated[str, typer.Argument(help="list | show | validate")],
        profile_name: Annotated[str | None, typer.Argument()] = None,
        policy_file: Annotated[Path | None, typer.Option("--file", help="Policy file path.")] = None,
        strict: Annotated[bool, typer.Option("--strict", help="Strict validation.")] = False,
    ) -> None:
        """List, show, or validate import policy profiles (Phase 11/15)."""
        import json as _json
        from sayane.core.import_policy import get_policy, list_policies

        if action == "list":
            names = list_policies()
            typer.echo(f"Available policies: {', '.join(names)}")
            return

        if action == "validate":
            if not policy_file:
                raise typer.BadParameter("--file required for validate")
            from sayane.core.policy_file import load_and_validate, resolve_effective_policy

            policy_data, errors = load_and_validate(policy_file)
            if errors:
                typer.echo("Invalid policy file:")
                for e in errors:
                    typer.echo(f"  - {e}")
                raise typer.Exit(2)
            effective = resolve_effective_policy(policy_data)
            typer.echo(f"Policy file valid: {policy_data['name']} (extends: {policy_data['extends']})")

        elif action == "show":
            if policy_file:
                from sayane.core.policy_file import load_and_validate, resolve_effective_policy
                policy_data, errors = load_and_validate(policy_file)
                if errors:
                    for e in errors:
                        typer.echo(f"Error: {e}", err=True)
                    raise typer.Exit(2)
                effective = resolve_effective_policy(policy_data)
                if effective:
                    typer.echo(_json.dumps(effective, ensure_ascii=False, indent=2))
                return

            if not profile_name:
                raise typer.BadParameter("profile name or --file required for 'show'")
            profile = get_policy(profile_name)
            if profile is None:
                typer.echo(f"Unknown policy: {profile_name}")
                return
            typer.echo(_json.dumps(profile, ensure_ascii=False, indent=2))
            return

        raise typer.BadParameter(f"Unknown action: {action}")

    @app.command()
    def key(
        action: Annotated[str, typer.Argument(help="generate | list")],
    ) -> None:
        """Generate or list Ed25519 signing keys (Phase 16)."""
        from sayane.core.signing import generate_keypair, list_keys

        if action == "generate":
            info = generate_keypair()
            typer.echo(f"Key generated: {info['key_id']}")
            typer.echo(f"  Private: {info['private_key_path']}")
            typer.echo(f"  Public:  {info['public_key_path']}")
        elif action == "list":
            keys = list_keys()
            if not keys:
                typer.echo("No keys found.")
            for k in keys:
                typer.echo(f"  {k['key_id']} (private: {k['has_private']})")
        else:
            raise typer.BadParameter(f"Unknown action: {action}")

    @app.command()
    def sign(
        bundle_path: Annotated[Path, typer.Argument(help="Bundle to sign.")],
        key_id: Annotated[str | None, typer.Option("--key", help="Key ID to sign with.")] = None,
    ) -> None:
        """Sign a context bundle (Phase 16)."""
        from sayane.core.import_bundle import parse_bundle
        from sayane.core.signing import sign_data, signed_payload_for_bundle, list_keys, verify_signature
        import yaml as _yaml

        if key_id is None:
            keys = list_keys()
            priv_keys = [k for k in keys if k["has_private"] == "True"]
            if not priv_keys:
                raise typer.BadParameter("No private keys found. Run 'sayane key generate' first.")
            key_id = priv_keys[0]["key_id"]

        parsed = parse_bundle(bundle_path)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle_path}")

        signed = sign_data(parsed, key_id, payload_fn=signed_payload_for_bundle)
        bundle_path.write_text(_yaml.safe_dump(signed, allow_unicode=True, sort_keys=False), encoding="utf-8")
        result = verify_signature(signed, payload_fn=signed_payload_for_bundle)
        typer.echo(f"Bundle signed: {key_id} → status: {result['status']}")

    @app.command()
    def package(
        action: Annotated[str, typer.Argument(help="create | inspect | verify")],
        path: Annotated[Path | None, typer.Argument()] = None,
        output: Annotated[Path, typer.Option("--output", "-o", help="Output directory.")] = Path("./sayane-export-package"),
        bundle: Annotated[Path | None, typer.Option("--bundle", help="Context bundle.")] = None,
        audit_export: Annotated[Path | None, typer.Option("--audit-export", help="Audit export file.")] = None,
        transfer_report: Annotated[Path | None, typer.Option("--transfer-report", help="Transfer report file.")] = None,
        policy_file: Annotated[Path | None, typer.Option("--policy-file", help="Policy file.")] = None,
        sign: Annotated[bool, typer.Option("--sign")] = False,
    ) -> None:
        """Create, inspect, or verify a signed export package (Phase 17)."""
        from sayane.core.export_package import create_package, inspect_package, verify_package

        if action == "create":
            artifacts: dict[str, Path] = {}
            if bundle: artifacts["bundle"] = bundle
            if audit_export: artifacts["audit"] = audit_export
            if transfer_report: artifacts["report"] = transfer_report
            if policy_file: artifacts["policy"] = policy_file

            manifest = create_package(
                output_dir=output,
                artifacts={k: v for k, v in artifacts.items() if v},
                sign=sign,
            )
            typer.echo(f"Package created: {output}")
            typer.echo(f"  Package ID: {manifest.get('package_id')}")
            typer.echo(f"  Artifacts: {manifest.get('summary', {}).get('artifact_count', 0)}")

        elif action == "inspect":
            pkg_dir = path or Path(".")
            manifest = inspect_package(pkg_dir)
            if manifest is None:
                typer.echo("Manifest missing or invalid.")
                return
            typer.echo(f"Package: {manifest.get('package_id')}")
            for art in manifest.get("artifacts", []):
                sig = art.get("signature", {}).get("status", "?")
                typer.echo(f"  {art['role']}: {art['path']} (sig: {sig})")

        elif action == "verify":
            pkg_dir = path or Path(".")
            result = verify_package(pkg_dir)
            typer.echo(f"Package verification: {result['status']}")
            for e in result["errors"]:
                typer.echo(f"  Error: {e}")
            for w in result["warnings"]:
                typer.echo(f"  Warning: {w}")

        else:
            raise typer.BadParameter(f"Unknown action: {action}")

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
