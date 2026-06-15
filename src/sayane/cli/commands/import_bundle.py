"""Import bundle command registration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated, Callable

import typer

from sayane.cli.i18n import t

LoadProfile = Callable[[Path | None], tuple[Path, object]]


def register_import_bundle(app: typer.Typer, load_profile_fn: LoadProfile) -> None:
    """Register the import-bundle command on the given Typer app."""

    @app.command()
    def import_bundle(
        bundle: Annotated[Path, typer.Argument(help="Path to portable context bundle (yaml/md).")],
        profile: Annotated[Path | None, typer.Option("--profile")] = None,
    ) -> None:
        """Import a portable context bundle as reviewable Candidates (#143)."""
        from sayane.core.import_bundle import import_bundle_with_semantic_review, parse_bundle

        _path, loaded = load_profile_fn(profile)
        parsed = parse_bundle(bundle)
        if parsed is None:
            raise typer.BadParameter(f"Could not parse bundle: {bundle}")

        # Bundle provenance verification (Phase 9)
        from sayane.core.bundle_provenance import verify_and_require_pass
        allowed, msg = verify_and_require_pass(parsed)
        typer.echo(f"Verification: {msg}")
        if not allowed:
            raise typer.BadParameter("Bundle verification failed. Import blocked.")

        candidates, review = import_bundle_with_semantic_review(parsed, loaded)
        if not candidates:
            typer.echo(t("import.no_candidates"))
            return
        typer.echo(t("import.candidates_header", count=len(candidates)))
        for i, c in enumerate(candidates):
            typer.echo(f"\n--- Candidate {i + 1} ---")
            typer.echo(f"  Section: {c['section']}")
            typer.echo(f"  Action:  {c['action']}")
            if c["current_value"]:
                typer.echo(f"  Current: {json.dumps(c['current_value'], ensure_ascii=False)[:120]}")
            typer.echo(f"  Proposed: {json.dumps(c['proposed_value'], ensure_ascii=False)[:120]}")
            # Semantic review flags (Phase 6)
            flags = review["candidate_flags"][i] if i < len(review["candidate_flags"]) else []
            if flags:
                typer.echo("  Flags:")
                for flag in flags:
                    typer.echo(f"    - {flag}")
            warnings = review["candidate_warnings"][i] if i < len(review["candidate_warnings"]) else []
            if warnings:
                typer.echo("  Warnings:")
                for w in warnings:
                    typer.echo(f"    - {w['message']}")

        # Cross-candidate overlap warnings
        overlaps = review.get("overlap_warnings", [])
        for ow in overlaps:
            typer.echo("\n--- Overlap Warning ---")
            typer.echo("  Terms:")
            for term in ow.get("terms", []):
                typer.echo(f"    - {term}")
            typer.echo(f"  Candidates: {', '.join(str(i + 1) for i in ow.get('candidate_indices', []))}")
            typer.echo(f"  Note: {ow.get('note', '')}")
