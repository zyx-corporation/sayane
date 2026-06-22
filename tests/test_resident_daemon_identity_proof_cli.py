"""Tests for resident daemon identity-proof CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sayane.cli.commands.app_daemon_identity_proof import (
    register_daemon_identity_proof_command,
)

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


@pytest.fixture
def app() -> typer.Typer:
    app_group = typer.Typer()
    register_daemon_identity_proof_command(app_group)
    return app_group


def test_daemon_identity_proof_json_uses_default_runtime_root(
    isolated_home: Path,
    app: typer.Typer,
) -> None:
    result = runner.invoke(app, ["--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_identity_proof_preview"
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["identity_status"] == "identity_not_running"
    assert payload["evidence_ceiling"] == "no_running_process"
    assert payload["proves_process_identity"] is False


def test_daemon_identity_proof_json_accepts_runtime_root_override(
    isolated_home: Path,
    tmp_path: Path,
    app: typer.Typer,
) -> None:
    runtime_root = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["identity"]["runtime_dir"] == str(runtime_root)
