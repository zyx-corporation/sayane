"""Tests for resident daemon runtime layout preview CLI (#196)."""

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


def test_daemon_runtime_layout_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-runtime-layout", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    runtime_root = isolated_home / ".sayane" / "run"
    assert payload == {
        "runtime_root": str(runtime_root),
        "pid_dir": str(runtime_root / "pid"),
        "lock_dir": str(runtime_root / "lock"),
        "socket_dir": str(runtime_root / "socket"),
        "log_dir": str(runtime_root / "log"),
        "temp_dir": str(runtime_root / "tmp"),
        "state_dir": str(runtime_root / "state"),
        "creates_directories": False,
        "writes_files": False,
        "is_filesystem_mutation": False,
        "kind": "resident_daemon_runtime_layout_preview",
        "preview_only": True,
    }
    assert runtime_root.exists() is False


def test_daemon_runtime_layout_json_accepts_runtime_root_override(
    isolated_home: Path,
    tmp_path: Path,
) -> None:
    runtime_root = tmp_path / "custom-runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-runtime-layout", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["runtime_root"] == str(runtime_root)
    assert payload["pid_dir"] == str(runtime_root / "pid")
    assert payload["lock_dir"] == str(runtime_root / "lock")
    assert payload["socket_dir"] == str(runtime_root / "socket")
    assert payload["log_dir"] == str(runtime_root / "log")
    assert payload["temp_dir"] == str(runtime_root / "tmp")
    assert payload["state_dir"] == str(runtime_root / "state")
    assert payload["creates_directories"] is False
    assert payload["writes_files"] is False
    assert payload["is_filesystem_mutation"] is False
    assert runtime_root.exists() is False
