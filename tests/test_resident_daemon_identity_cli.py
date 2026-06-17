"""Tests for resident daemon identity preview CLI (#192)."""

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


def test_daemon_identity_json_uses_default_runtime_dir(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-identity", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_dir = isolated_home / ".sayane" / "run"
    assert payload == {
        "name": "sayane-resident",
        "runtime_dir": str(runtime_dir),
        "pid_path": str(runtime_dir / "sayane-resident.pid"),
        "lock_path": str(runtime_dir / "sayane-resident.lock"),
        "socket_path": str(runtime_dir / "sayane-resident.sock"),
        "writes_files": False,
        "acquires_lock": False,
        "stale_lock_policy": "manual_review_required",
        "is_process_control": False,
        "kind": "resident_daemon_identity_preview",
        "preview_only": True,
    }
    assert runtime_dir.exists() is False


def test_daemon_identity_json_accepts_runtime_dir_override(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_dir = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-identity", "--runtime-dir", str(runtime_dir), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["runtime_dir"] == str(runtime_dir)
    assert payload["pid_path"] == str(runtime_dir / "sayane-resident.pid")
    assert payload["lock_path"] == str(runtime_dir / "sayane-resident.lock")
    assert payload["socket_path"] == str(runtime_dir / "sayane-resident.sock")
    assert payload["writes_files"] is False
    assert payload["acquires_lock"] is False
    assert runtime_dir.exists() is False
