"""Tests for resident daemon readiness diagnostic CLI."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


def test_daemon_readiness_diagnostic_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-readiness-diagnostic", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_readiness_diagnostic_preview"
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["operation_class"] == "bridge_health"
    assert payload["readiness_status"] == "readiness_not_ready"
    assert payload["api_readiness_status"] == "api_unreachable"


def test_daemon_readiness_diagnostic_json_accepts_operation_class(
    isolated_home: Path,
) -> None:
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-readiness-diagnostic",
            "--operation-class",
            "diagnostics",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["operation_class"] == "diagnostics"
