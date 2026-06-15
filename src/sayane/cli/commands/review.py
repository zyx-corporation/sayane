"""Review and audit command registration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer


def register_review(app: typer.Typer) -> None:
    """Register review, context-compile, and audit commands."""

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
                    typer.echo("  Warnings:")
                    for w in d.review_warnings:
                        typer.echo(f"    - {w.get('message', w)}")
                if d.transfer_path:
                    typer.echo(f"  Transfer path: {' → '.join(d.transfer_path)}")
                typer.echo(f"  Reason:  {d.reason or 'N/A'}")
                if d.applied_value:
                    typer.echo(f"  Applied: {_json.dumps(d.applied_value, ensure_ascii=False)[:120]}")
                if d.decision == "scoped_accept":
                    if d.accepted_scope:
                        typer.echo(f"  Scope:   {d.accepted_scope.get('level', '?')}:{d.accepted_scope.get('target', '?')}:{d.accepted_scope.get('sub_scope', '?')}")
                    if d.conditions:
                        typer.echo("  Conditions:")
                        for c in d.conditions:
                            typer.echo(f"    - {c}")
                    if d.negative_constraints:
                        typer.echo("  Must NOT:")
                        for nc in d.negative_constraints:
                            typer.echo(f"    - {nc}")
                    pp = d.promotion_policy or {}
                    if pp.get("can_promote") is False:
                        typer.echo("  Promotion: blocked (requires review)")
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
            for r in records[-20:]:
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
