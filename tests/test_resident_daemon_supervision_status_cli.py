"""CLI tests for resident daemon supervision status."""

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


def test_daemon_supervision_status_json_uses_default_runtime_root(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-supervision-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_supervision_status"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["background_surfaces"]["status"] == "not_supported"
    assert payload["background_surfaces"]["candidate_surfaces"][0]["surface"] == "tray_supervision"


def test_daemon_supervision_status_text_exposes_post_app_detail_surface(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-supervision-status"])

    assert result.exit_code == 0
    assert "phase_status: decision_line_partially_defined" in result.stdout
    assert "passive_visibility_status: supported" in result.stdout
    assert "active_supervision_status: limited_cli_only" in result.stdout
    assert "passive_visibility_surfaces:" in result.stdout
    assert "active_supervision_actions:" in result.stdout
    assert "deferred_background_topics:" in result.stdout
    assert "candidate_background_surfaces:" in result.stdout
    assert "tray_supervision: separate_plan_required" in result.stdout
    assert "decision_guardrails:" in result.stdout
