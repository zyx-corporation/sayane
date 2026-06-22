"""CLI tests for resident daemon repair apply."""

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


def test_daemon_repair_apply_json_no_action_without_targets(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-repair-apply", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_repair_apply_receipt"
    assert payload["result"] == "no_action"
    assert payload["applied"] is False


def test_daemon_repair_preview_json_exposes_confirmation_fields(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-repair-preview", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_repair_apply_preview"
    assert payload["operation_id"].startswith("repair-preview-")
    assert len(payload["preview_hash"]) == 16
