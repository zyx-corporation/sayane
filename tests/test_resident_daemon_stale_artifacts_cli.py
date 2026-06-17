"""Tests for resident daemon stale artifact diagnostic CLI (#199)."""

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


def test_daemon_stale_artifacts_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-stale-artifacts", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_stale_artifact_diagnostic_preview"
    assert payload["preview_only"] is True
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["stale_artifact_policy"] == "manual_review_required"
    assert payload["repairs_artifacts"] is False
    assert payload["deletes_artifacts"] is False
    assert payload["creates_artifacts"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["manual_review_required"] is False
    assert len(payload["diagnostics"]) == 10
    assert runtime_root.exists() is False


def test_daemon_stale_artifacts_json_accepts_runtime_root_override(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-stale-artifacts", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["runtime_root"] == str(runtime_root)
    assert len(payload["diagnostics"]) == 10
    assert all(diagnostic["exists"] is False for diagnostic in payload["diagnostics"])
    assert runtime_root.exists() is False


def test_daemon_stale_artifacts_json_reports_existing_pid_file(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["app", "daemon-stale-artifacts", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    pid_diagnostic = next(
        diagnostic for diagnostic in payload["diagnostics"] if diagnostic["kind"] == "pid_file"
    )
    assert payload["manual_review_required"] is True
    assert pid_diagnostic["exists"] is True
    assert pid_diagnostic["status"] == "present_review_required"
    assert pid_diagnostic["manual_review_required"] is True
    assert pid_diagnostic["safe_to_delete"] is False
    assert pid_path.exists() is True
