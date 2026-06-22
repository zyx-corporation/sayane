"""CLI tests for resident daemon packaging status."""

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


def test_daemon_packaging_status_json_uses_default_runtime_root(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-packaging-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_packaging_status"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["packaging_model"] == "cli_first_local_bridge"
