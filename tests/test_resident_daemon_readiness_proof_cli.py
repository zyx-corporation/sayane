"""Tests for resident daemon readiness-proof CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sayane.cli.commands.app_daemon_readiness_proof import (
    register_daemon_readiness_proof_command,
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
    register_daemon_readiness_proof_command(app_group)
    return app_group


def test_daemon_readiness_proof_json_uses_default_runtime_root(
    isolated_home: Path,
    app: typer.Typer,
) -> None:
    result = runner.invoke(app, ["--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_readiness_proof_preview"
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["readiness_status"] == "readiness_not_ready"
    assert payload["evidence_ceiling"] == "no_running_process"


def test_daemon_readiness_proof_json_accepts_operation_class(
    isolated_home: Path,
    app: typer.Typer,
) -> None:
    result = runner.invoke(
        app,
        ["--operation-class", "diagnostics", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["operation_class"] == "diagnostics"
