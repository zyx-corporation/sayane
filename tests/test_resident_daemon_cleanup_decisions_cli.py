"""Tests for resident daemon cleanup decision CLI (#200)."""

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


def test_daemon_cleanup_decisions_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-cleanup-decisions", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload["kind"] == "resident_daemon_cleanup_decision_preview"
    assert payload["preview_only"] is True
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["decision_policy"] == "manual_review_required"
    assert payload["deletes_artifacts"] is False
    assert payload["repairs_artifacts"] is False
    assert payload["mutates_filesystem"] is False
    assert payload["manual_review_required"] is False
    assert len(payload["decisions"]) == 10
    assert all(decision["recommendation"] == "no_action" for decision in payload["decisions"])
    assert runtime_root.exists() is False


def test_daemon_cleanup_decisions_json_accepts_runtime_root_override(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-cleanup-decisions", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["runtime_root"] == str(runtime_root)
    assert len(payload["decisions"]) == 10
    assert all(decision["recommendation"] == "no_action" for decision in payload["decisions"])
    assert runtime_root.exists() is False


def test_daemon_cleanup_decisions_json_requires_review_for_present_pid_file(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    pid_path = runtime_root / "sayane-resident.pid"
    pid_path.write_text("12345\n", encoding="utf-8")

    result = runner.invoke(
        app,
        ["app", "daemon-cleanup-decisions", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    pid_decision = next(
        decision for decision in payload["decisions"] if decision["artifact_kind"] == "pid_file"
    )
    assert payload["manual_review_required"] is True
    assert pid_decision["recommendation"] == "manual_review_required"
    assert pid_decision["safe_to_delete"] is False
    assert pid_decision["deletes_artifact"] is False
    assert pid_path.exists() is True
