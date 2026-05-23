"""CLI for Candidate Update evaluation and approval."""

import json
from typing import Annotated

import typer
import yaml

from omomuki.bridge.config import BridgeConfig
from omomuki.evaluators.service import (
    approve_candidate,
    diff_candidate,
    evaluate_candidate,
    reject_candidate,
)
from omomuki.storage.candidates import list_candidate_ids, load_candidate
from omomuki.storage.lineage_store import list_records

candidate_app = typer.Typer(help="Candidate updates (RDE / approve flow).", no_args_is_help=True)


def _config() -> BridgeConfig:
    return BridgeConfig()


@candidate_app.command("list")
def candidate_list() -> None:
    """List candidate update ids."""
    ids = list_candidate_ids(_config())
    if not ids:
        typer.echo("No candidates.")
        raise typer.Exit(0)
    for cid in ids:
        try:
            c = load_candidate(_config(), cid)
            rde = c.evaluation.rde_class if c.evaluation else "-"
            typer.echo(f"{cid}\t{c.status}\t{rde}")
        except Exception:
            typer.echo(f"{cid}\t?")

@candidate_app.command("show")
def candidate_show(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
    """Show full candidate record."""
    candidate = load_candidate(_config(), candidate_id)
    typer.echo(yaml.safe_dump(candidate.model_dump(mode="json"), allow_unicode=True))


@candidate_app.command("evaluate")
def candidate_evaluate(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
    """Run heuristic RDE + UIB evaluation."""
    candidate = evaluate_candidate(_config(), candidate_id)
    typer.echo(yaml.safe_dump(candidate.evaluation.model_dump(mode="json"), allow_unicode=True))


@candidate_app.command("approve")
def candidate_approve(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
    """Approve and merge into profile (knowledge.concepts only in MVP)."""
    try:
        candidate = approve_candidate(_config(), candidate_id)
        typer.echo(f"Approved and merged: {candidate.id} → {candidate.target_profile_id}")
    except ValueError as exc:
        raise typer.BadParameter(str(exc)) from exc


@candidate_app.command("reject")
def candidate_reject(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
    reason: Annotated[str | None, typer.Option("--reason")] = None,
) -> None:
    """Reject candidate without merging."""
    candidate = reject_candidate(_config(), candidate_id, reason=reason)
    typer.echo(f"Rejected: {candidate.id}")


@candidate_app.command("diff")
def candidate_diff(
    candidate_id: Annotated[str, typer.Argument(help="Candidate id")],
) -> None:
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
        typer.echo("No lineage records.")
        raise typer.Exit(0)
    for rec in records:
        typer.echo(json.dumps(rec, ensure_ascii=False))
