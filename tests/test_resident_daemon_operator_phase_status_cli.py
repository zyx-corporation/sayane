"""CLI tests for resident daemon operator phase status."""

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


def test_daemon_operator_phase_status_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-operator-phase-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_operator_phase_status"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["phase"] == "operator_packaging_and_supervision"
    assert payload["phase_readiness"] == "not_ready_for_phase_closure"
