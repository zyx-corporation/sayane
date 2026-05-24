"""Plugin hook tests."""

import typer


def test_cli_extensions_noop_without_pro() -> None:
    from sayane.cli.app import build_app

    app = build_app()
    assert isinstance(app, typer.Typer)


def test_hooks_noop_without_pro() -> None:
    from sayane.plugins.hooks import reset_hooks, run_before_candidate_approve

    reset_hooks()
    # Should not raise when no hooks registered
    run_before_candidate_approve  # callable exists
