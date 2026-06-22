"""CLI tests for daemon service target status."""

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


def test_daemon_service_targets_status_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-service-targets-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_service_targets_status"
    assert len(payload["targets"]) == 3
    assert payload["policy_gates"]["hybrid_packaging_gate"] == (
        "service_lifecycle_and_platform_policy_closure_required"
    )
