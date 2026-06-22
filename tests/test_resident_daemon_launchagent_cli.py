"""CLI tests for LaunchAgent preview/apply commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.app import build_launchagent_plan
from sayane.cli.main import app

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: home)
    return home


def test_daemon_launchagent_preview_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-launchagent-preview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_launchagent_plan"


def test_daemon_launchagent_apply_json(isolated_home: Path) -> None:
    plan = build_launchagent_plan(isolated_home / ".sayane" / "run", sayane_home=isolated_home / ".sayane")
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-launchagent-apply",
            "--operation-id",
            plan.operation_id,
            "--confirm-operation-id",
            plan.operation_id,
            "--confirm-preview-hash",
            plan.preview_hash(),
            "--json",
        ],
    )

    assert result.exit_code == 0
    assert json.loads(result.stdout)["kind"] == "resident_daemon_launchagent_receipt"
