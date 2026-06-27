"""Review and audit command registration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Any

import typer

from sayane.cli.runtime_config import CliVaultMode, resolve_cli_bridge_config
from sayane.core.audit_trail import build_audit_record, get_audit_store
from sayane.storage.review_decisions import append_review_decision, list_review_decisions
from sayane.vault.unlock_policy import UnlockLevel


class _DerivedAuditStore:
    """Minimal read-only audit store view derived from review decisions."""

    def __init__(self, records: list[dict[str, Any]]) -> None:
        self._records = list(records)

    def read_all(self) -> list[dict[str, Any]]:
        return list(self._records)


def register_review(app: typer.Typer) -> None:
    """Register review, context-compile, and audit commands."""

    def _config(
        *,
        vault_mode: CliVaultMode | None,
        vault_sqlite: str | None,
        unlock_level: UnlockLevel | None,
        purpose: str,
    ):
        sqlite_path = Path(vault_sqlite) if vault_sqlite else None
        return resolve_cli_bridge_config(
            vault_mode=vault_mode,
            vault_sqlite=sqlite_path,
            unlock_level=unlock_level,
            unlock_purpose=purpose,
        )

    def _read_decisions(
        *,
        vault_mode: CliVaultMode | None,
        vault_sqlite: str | None,
        unlock_level: UnlockLevel | None,
        purpose: str,
        profile_id: str = "default",
    ):
        cfg = _config(
            vault_mode=vault_mode,
            vault_sqlite=vault_sqlite,
            unlock_level=unlock_level,
            purpose=purpose,
        )
        return list_review_decisions(cfg, profile_id)

    def _write_decision(
        decision,
        *,
        vault_mode: CliVaultMode | None,
        vault_sqlite: str | None,
        unlock_level: UnlockLevel | None,
        purpose: str,
        profile_id: str = "default",
    ):
        cfg = _config(
            vault_mode=vault_mode,
            vault_sqlite=vault_sqlite,
            unlock_level=unlock_level,
            purpose=purpose,
        )
        append_review_decision(cfg, profile_id, decision)
        return cfg

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
        """Review import candidates (Phase 7/12)."""
        import json as _json
        from sayane.core.review_decision import (
            ReviewDecision,
            get_overlap_resolution,
            validate_decision,
        )

        if action == "list":
            decisions = _read_decisions(
                vault_mode=vault_mode,
                vault_sqlite=vault_sqlite,
                unlock_level=unlock_level,
                purpose="cli-review-list",
            )
            if not decisions:
                typer.echo("No review decisions recorded.")
                return
            filtered = decisions
            if filter_flag:
                filtered = [d for d in decisions if filter_flag in (d.review_flags or [])]
            typer.echo(f"{len(filtered)} review decision(s):")
            for item in filtered:
                applied = f" → {_json.dumps(item.applied_value, ensure_ascii=False)[:80]}" if item.applied_value else ""
                flags = f" [{', '.join(item.review_flags)}]" if item.review_flags else ""
                typer.echo(f"  [{item.decision.upper()}] {item.candidate_id} ({item.original_section}) — {item.reason[:60]}{applied}{flags}")
            return

        if action == "show":
            if not candidate_id:
                raise typer.BadParameter("candidate_id required for show")
            decisions = [
                item
                for item in _read_decisions(
                    vault_mode=vault_mode,
                    vault_sqlite=vault_sqlite,
                    unlock_level=unlock_level,
                    purpose="cli-review-show",
                )
                if item.candidate_id == candidate_id
            ]
            decision_item = decisions[-1] if decisions else None
            typer.echo(f"=== Candidate Detail: {candidate_id} ===")
            if decision_item:
                typer.echo(f"  Section: {decision_item.original_section}")
                typer.echo(f"  Action:  {decision_item.original_action}")
                typer.echo(f"  Decision: {decision_item.decision.upper()}")
                if decision_item.review_flags:
                    typer.echo(f"  Flags:   {', '.join(decision_item.review_flags)}")
                if decision_item.review_warnings:
                    typer.echo("  Warnings:")
                    for warning in decision_item.review_warnings:
                        typer.echo(f"    - {warning.get('message', warning)}")
                if decision_item.transfer_path:
                    typer.echo(f"  Transfer path: {' → '.join(decision_item.transfer_path)}")
                typer.echo(f"  Reason:  {decision_item.reason or 'N/A'}")
                if decision_item.applied_value:
                    typer.echo(f"  Applied: {_json.dumps(decision_item.applied_value, ensure_ascii=False)[:120]}")
                if decision_item.decision == "scoped_accept":
                    if decision_item.accepted_scope:
                        typer.echo(
                            "  Scope:   "
                            f"{decision_item.accepted_scope.get('level', '?')}:"
                            f"{decision_item.accepted_scope.get('target', '?')}:"
                            f"{decision_item.accepted_scope.get('sub_scope', '?')}"
                        )
                    if decision_item.conditions:
                        typer.echo("  Conditions:")
                        for condition in decision_item.conditions:
                            typer.echo(f"    - {condition}")
                    if decision_item.negative_constraints:
                        typer.echo("  Must NOT:")
                        for constraint in decision_item.negative_constraints:
                            typer.echo(f"    - {constraint}")
                    promotion_policy = decision_item.promotion_policy or {}
                    if promotion_policy.get("can_promote") is False:
                        typer.echo("  Promotion: blocked (requires review)")
                typer.echo(f"  Lineage: {decision_item.lineage_event_id[:12]}")
            else:
                typer.echo("  No decisions recorded. Import a bundle first, then use review approve/reject/modify/defer.")
            return

        if action == "overlap":
            if candidate_id:
                resolution = get_overlap_resolution(candidate_id)
                if resolution:
                    typer.echo(f"Overlap Group: {resolution.overlap_id}")
                    typer.echo(f"  Terms: {', '.join(resolution.terms)}")
                    typer.echo(f"  Candidates: {', '.join(resolution.candidate_ids)}")
                    typer.echo(f"  Resolved: {resolution.resolved}")
                    if resolution.resolution_reason:
                        typer.echo(f"  Reason: {resolution.resolution_reason}")
                else:
                    typer.echo("Overlap group not found.")
            else:
                typer.echo("Usage: sayane review overlap <overlap-id>")
            return

        if action == "diff":
            if not candidate_id:
                raise typer.BadParameter("candidate_id required for diff")
            from sayane.core.decision_diff import build_decision_diff, render_diff

            decisions = [
                item
                for item in _read_decisions(
                    vault_mode=vault_mode,
                    vault_sqlite=vault_sqlite,
                    unlock_level=unlock_level,
                    purpose="cli-review-diff",
                )
                if item.candidate_id == candidate_id
            ]
            if not decisions:
                typer.echo("No decisions recorded. Import and review a candidate first.")
                return
            decision_item = decisions[-1]
            diff = build_decision_diff(
                candidate_id=decision_item.candidate_id,
                decision=decision_item.decision,
                section=decision_item.original_section,
                original_candidate=decision_item.original_proposed,
                applied_value=decision_item.applied_value,
                reason=decision_item.reason,
                warnings_in=decision_item.review_warnings,
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
            condition_list = [item.strip() for item in (conditions or "").split(",") if item.strip()]
            negative_list = [item.strip() for item in (negative or "").split(",") if item.strip()]
            decision_item = ReviewDecision(
                candidate_id=candidate_id,
                decision="scoped_accept",
                reason=reason or "",
                accepted_scope=accepted_scope,
                conditions=condition_list,
                negative_constraints=negative_list,
                promotion_policy={"can_promote": False},
                reuse_policy={"review_on_reuse": True},
            )
            errors = validate_decision(decision_item, has_review_required=True)
            if errors:
                for error in errors:
                    typer.echo(f"Error: {error}", err=True)
                raise typer.Exit(1)
            _write_decision(
                decision_item,
                vault_mode=vault_mode,
                vault_sqlite=vault_sqlite,
                unlock_level=unlock_level,
                purpose="cli-review-scoped-accept",
            )
            typer.echo(f"Scoped accept: {candidate_id} → {accepted_scope}")
            return

        applied_value = None
        if value:
            try:
                applied_value = _json.loads(value)
            except _json.JSONDecodeError as exc:
                raise typer.BadParameter(f"Invalid JSON for --value: {value}") from exc

        decision_item = ReviewDecision(
            candidate_id=candidate_id,
            decision=action,  # type: ignore[arg-type]
            reason=reason or "",
            applied_value=applied_value,
            original_section="imported",
            original_action="add",
        )

        errors = validate_decision(decision_item, has_review_required=("review_required" in (reason or "")))
        if errors:
            for error in errors:
                typer.echo(f"Error: {error}", err=True)
            raise typer.Exit(1)

        cfg = _write_decision(
            decision_item,
            vault_mode=vault_mode,
            vault_sqlite=vault_sqlite,
            unlock_level=unlock_level,
            purpose=f"cli-review-{action}",
        )
        typer.echo(f"Decision recorded: [{decision_item.decision.upper()}] {candidate_id} — lineage event: {decision_item.lineage_event_id[:12]}")

        if cfg.repositories is None:
            store = get_audit_store()
            audit = build_audit_record(decision_item, profile_updated=(action in ("approve", "modify")))
            store.append(audit)
            typer.echo(f"Audit: appended to {store.path}")
        else:
            typer.echo("Audit: derived from vault-backed review decisions")

    @app.command()
    def context_compile(
        target: Annotated[str, typer.Option("--target", help="Target tool: cursor | claude-desktop")] = "cursor",
        mode: Annotated[str, typer.Option("--mode", help="Output mode: compact | full | strict")] = "full",
        show_scope: Annotated[bool, typer.Option("--show-scope")] = False,
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
        """Compile MCP context with scoped accept metadata (F-2)."""
        from sayane.core.mcp_context import build_compiled_context, render_compiled_context_text

        scoped = [
            item
            for item in _read_decisions(
                vault_mode=vault_mode,
                vault_sqlite=vault_sqlite,
                unlock_level=unlock_level,
                purpose="cli-context-compile",
            )
            if item.decision == "scoped_accept"
        ]
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
        """Query the review decision audit trail (Phase 8)."""
        if vault_mode is None:
            store = get_audit_store()
            records = store.read_all()
        else:
            records = [
                build_audit_record(
                    item,
                    profile_updated=(item.decision in ("approve", "modify")),
                )
                for item in _read_decisions(
                    vault_mode=vault_mode,
                    vault_sqlite=vault_sqlite,
                    unlock_level=unlock_level,
                    purpose="cli-audit-read",
                )
            ]
            store = _DerivedAuditStore(records)

        if action == "list":
            if not records:
                typer.echo("No audit records.")
                return
            typer.echo(f"{len(records)} audit record(s):")
            for record in records[-20:]:
                record_decision = record["decision"]
                record_candidate = record["candidate"]
                applied = (
                    f" → {json.dumps(record['result']['applied_value'], ensure_ascii=False)[:60]}"
                    if record["result"]["applied_value"]
                    else ""
                )
                typer.echo(f"  [{record_decision['type'].upper()}] {record_candidate['section']} — {record_decision['reason'][:60]}{applied}")

        elif action == "by-candidate":
            if not query_value:
                raise typer.BadParameter("candidate_id required for by-candidate")
            matches = [record for record in records if record.get("candidate", {}).get("id") == query_value]
            typer.echo(f"{len(matches)} record(s) for candidate {query_value}:")
            for record in matches:
                typer.echo(f"  [{record['decision']['type'].upper()}] {record['decision']['reason'][:80]}")

        elif action == "by-term":
            if not query_value:
                raise typer.BadParameter("term required for by-term")
            matches = [
                record
                for record in records
                if query_value.lower() in json.dumps(record.get("candidate", {}).get("proposed"), ensure_ascii=False).lower()
                or any(query_value.lower() in warning.get("term", "").lower() for warning in record.get("candidate", {}).get("warnings", []))
            ]
            typer.echo(f"{len(matches)} record(s) for term '{query_value}':")
            for record in matches:
                typer.echo(f"  [{record['decision']['type'].upper()}] {record['candidate']['section']} — flags={record['candidate'].get('flags', [])}")

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
