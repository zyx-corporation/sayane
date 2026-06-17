"""Tests for resident daemon PID file diagnostic CLI (#202)."""

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


def test_daemon_pid_diagnostic_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-pid-diagnostic", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_pid_file_parse_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["path"] == str(runtime_root / "sayane-resident.pid")
    assert payload["exists"] is False
    assert payload["status"] == "missing"
    assert payload["parsed_pid"] is None
    assert payload["manual_review_required"] is False
    assert payload["proves_liveness"] is False
    assert payload["probes_process"] is False
    assert payload["controls_process"] is False
    assert payload["mutates_filesystem"] is False
    assert runtime_root.exists() is False


def test_daemon_pid_diagnostic_json_accepts_runtime_root_override(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-pid-diagnostic", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["path"] == str(runtime_root / "sayane-resident.pid")
    assert payload["status"] == "missing"
    assert runtime_root.exists() is False


def test_daemon_pid_diagnostic_json_reports_parsed_pid(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["app", "daemon-pid-diagnostic", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["exists"] is True
    assert payload["status"] == "parsed"
    assert payload["parsed_pid"] == 12345
    assert payload["manual_review_required"] is True
    assert payload["proves_liveness"] is False
    assert payload["controls_process"] is False
    assert pid_path.exists() is True
