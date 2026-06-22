"""Tests for resident daemon aggregated proof diagnostics CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from sayane.cli.commands.app_daemon_proof_diagnostics import (
    register_daemon_proof_diagnostics_command,
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
    register_daemon_proof_diagnostics_command(app_group)
    return app_group


def test_daemon_proof_diagnostics_json_aggregates_three_proof_payloads(
    isolated_home: Path,
    app: typer.Typer,
) -> None:
    result = runner.invoke(app, ["--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_proof_diagnostics_preview"
    assert payload["preview_only"] is True
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["identity_proof"]["kind"] == "resident_daemon_identity_proof_preview"
    assert payload["readiness_proof"]["kind"] == "resident_daemon_readiness_proof_preview"
    assert payload["api_readiness_proof"]["kind"] == "resident_daemon_api_readiness_proof_preview"
    assert payload["mutates_filesystem"] is False
    assert payload["controls_process"] is False


def test_daemon_proof_diagnostics_json_accepts_operation_class(
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
    assert payload["readiness_proof"]["operation_class"] == "diagnostics"
    assert payload["api_readiness_proof"]["operation_class"] == "diagnostics"
