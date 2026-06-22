"""CLI tests for resident daemon service/control boundary command."""

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


def test_daemon_service_control_boundary_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-service-control-boundary", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_service_control_boundary"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["service_plane"]["status"] == "not_supported"

