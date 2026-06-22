"""CLI tests for resident daemon overview preview."""

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


def test_daemon_overview_json_uses_default_runtime_root(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-overview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_overview_preview"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["status"]["state"] == "stopped"

