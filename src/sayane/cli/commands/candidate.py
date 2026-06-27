"""Candidate command group registration."""

from __future__ import annotations

import json
from typing import Annotated

import typer
import yaml

from sayane.cli.i18n import t
from sayane.cli.runtime_config import CliVaultMode, resolve_cli_bridge_config
from sayane.vault.unlock_policy import UnlockLevel


def register_candidate(app: typer.Typer) -> None:
    """Register candidate commands on the given Typer app."""
    from sayane.evaluators.service import (
        approve_candidate,
        diff_candidate,
        evaluate_candidate,
        reject_candidate,
    )
    from sayane.storage.candidates import list_candidate_ids, load_candidate
    from sayane.storage.lineage_store import list_records

    candidate_app = typer.Typer(help=t("group.candidate"), no_args_is_help=True)

    vault_state: dict[str, object] = {}

    @candidate_app.callback()
    def candidate_options(
        ctx: typer.Context,
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
        del ctx
        vault_state["vault_mode"] = vault_mode
        vault_state["vault_sqlite"] = vault_sqlite
        vault_state["unlock_level"] = unlock_level

    def _config(*, purpose: str) -> object:
        from pathlib import Path

        sqlite_raw = vault_state.get("vault_sqlite")
        sqlite_path = Path(sqlite_raw) if isinstance(sqlite_raw, str) and sqlite_raw else None
        return resolve_cli_bridge_config(
            vault_mode=vault_state.get("vault_mode"),  # type: ignore[arg-type]
            vault_sqlite=sqlite_path,
            unlock_level=vault_state.get("unlock_level"),  # type: ignore[arg-type]
            unlock_purpose=purpose,
        )

    @candidate_app.command("list")
    def candidate_list() -> None:
        """List candidate update ids."""
        cfg = _config(purpose="cli-candidate-list")
        ids = list_candidate_ids(cfg)
        if not ids:
            typer.echo(t("candidate.none"))
            raise typer.Exit(0)
        for cid in ids:
            try:
                c = load_candidate(cfg, cid)
                rde = c.evaluation.rde_class if c.evaluation else "-"
                typer.echo(f"{cid}\t{c.status}\t{rde}")
            except Exception:
                typer.echo(f"{cid}\t?")

    @candidate_app.command("show")
    def candidate_show(candidate_id: Annotated[str, typer.Argument()]) -> None:
        """Show full candidate record."""
        candidate = load_candidate(_config(purpose="cli-candidate-show"), candidate_id)
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
        candidate = evaluate_candidate(_config(purpose="cli-candidate-evaluate"), candidate_id, level=level)
        typer.echo(yaml.safe_dump(candidate.evaluation.model_dump(mode="json"), allow_unicode=True))

    @candidate_app.command("approve")
    def candidate_approve(
        candidate_id: Annotated[str, typer.Argument()],
        force_critical: Annotated[bool, typer.Option("--force-critical")] = False,
    ) -> None:
        """Approve and merge into profile."""
        try:
            candidate = approve_candidate(
                _config(purpose="cli-candidate-approve"),
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
        candidate = reject_candidate(_config(purpose="cli-candidate-reject"), candidate_id, reason=reason)
        typer.echo(t("candidate.rejected", id=candidate.id))

    @candidate_app.command("diff")
    def candidate_diff(candidate_id: Annotated[str, typer.Argument()]) -> None:
        """Show rule-based diff vs current profile."""
        result = diff_candidate(_config(purpose="cli-candidate-diff"), candidate_id)
        typer.echo(json.dumps(result, ensure_ascii=False, indent=2))

    @candidate_app.command("lineage")
    def candidate_lineage(
        profile_id: Annotated[str, typer.Option("--profile-id")] = "default",
        limit: Annotated[int, typer.Option("--limit")] = 20,
    ) -> None:
        """Show recent lineage records for a profile."""
        records = list_records(_config(purpose="cli-candidate-lineage"), profile_id, limit=limit)
        if not records:
            typer.echo(t("candidate.lineage_none"))
            raise typer.Exit(0)
        for rec in records:
            typer.echo(json.dumps(rec, ensure_ascii=False))

    app.add_typer(candidate_app, name="candidate")
