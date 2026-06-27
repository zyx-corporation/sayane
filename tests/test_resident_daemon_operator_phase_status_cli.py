"""CLI tests for resident daemon operator phase status."""

from __future__ import annotations

import sys
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
    assert payload["phase_readiness"] == "ready_for_mvp_release_closure"


def test_daemon_operator_phase_status_text_exposes_post_app_detail_surface(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-operator-phase-status"])

    assert result.exit_code == 0
    assert "kind: resident_daemon_operator_phase_status" in result.stdout
    assert "phase_readiness: ready_for_mvp_release_closure" in result.stdout
    assert (
        "startup_command: ./scripts/run-macos-app-preview.sh" in result.stdout
        if sys.platform == "darwin"
        else "startup_command: sayane serve --host 127.0.0.1 --port 38741" in result.stdout
    )
    assert "primary_operator_ui:" in result.stdout
    assert "debug_operator_ui: bridge_hosted_debug_shell" in result.stdout
    assert "recommended_launcher:" in result.stdout
    assert "bootstrap_ui: http://127.0.0.1:38741/app/ui" in result.stdout
    assert "blocking_reasons:" in result.stdout
    assert "workstreams:" in result.stdout
    assert "packaging_model_decision: closed_for_mvp" in result.stdout
    assert "decision_assist:" in result.stdout
    assert "closure_evidence:" in result.stdout
    assert "read_surfaces:" in result.stdout
    assert "sayane app daemon-operator-phase-status --json" in result.stdout
    assert "exit_criteria:" in result.stdout
    assert "not_in_scope:" in result.stdout
