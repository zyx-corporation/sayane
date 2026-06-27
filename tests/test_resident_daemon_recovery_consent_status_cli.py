"""CLI tests for resident daemon recovery/consent status."""

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


def test_daemon_recovery_consent_status_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-recovery-consent-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_recovery_consent_status"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["consent_model"] == "explicit_cli_confirmation_for_mutation"


def test_daemon_recovery_consent_status_text_exposes_post_app_detail_surface(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-recovery-consent-status"])

    assert result.exit_code == 0
    assert "phase_status: mvp_boundary_finalized" in result.stdout
    assert "non_mutating_diagnostics:" in result.stdout
    assert "mutating_recovery_actions:" in result.stdout
    assert "sayane app daemon-cleanup-apply --json" in result.stdout
    assert "control_recovery_actions:" in result.stdout
    assert "sayane app daemon-start --json" in result.stdout
    assert "runtime init must already be complete" in result.stdout
    assert "app_ui_guardrails:" in result.stdout
    assert "recommended_recovery_flow:" in result.stdout
