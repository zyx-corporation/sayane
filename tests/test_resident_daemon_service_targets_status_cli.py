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
    assert payload["policy_gates"]["hybrid_packaging_gate"] == "post_mvp_only"


def test_daemon_service_targets_status_text_exposes_post_app_detail_surface(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-service-targets-status"])

    assert result.exit_code == 0
    assert "platform_policy_required: True" in result.stdout
    assert "rollback_policy_required: True" in result.stdout
    assert "hybrid_packaging_gate: post_mvp_only" in result.stdout
    assert "targets:" in result.stdout
    assert "macos_launchagent:" in result.stdout
    assert "linux_systemd_user:" in result.stdout
    assert "windows_service:" in result.stdout
