"""Tests for resident daemon runtime init CLI."""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


def test_daemon_runtime_init_json_preview_does_not_create_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        ["app", "daemon-runtime-init", "--runtime-root", str(runtime_root), "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_runtime_init_plan"
    assert payload["preview_only"] is True
    assert payload["mutates_filesystem"] is False
    assert payload["review_required"] is False
    assert runtime_root.exists() is False


def test_daemon_runtime_init_apply_creates_directories(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--apply",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_runtime_init_apply"
    assert payload["applied"] is True
    assert len(payload["created_paths"]) == 7
    assert (runtime_root / "state").is_dir()


def test_daemon_runtime_init_apply_rejects_conflicting_paths(tmp_path: Path) -> None:
    runtime_root = tmp_path / "runtime"
    runtime_root.mkdir()
    (runtime_root / "pid").write_text("conflict", encoding="utf-8")

    result = runner.invoke(
        app,
        [
            "app",
            "daemon-runtime-init",
            "--runtime-root",
            str(runtime_root),
            "--apply",
        ],
    )

    assert result.exit_code != 0
    combined = result.stdout + (result.stderr or "")
    assert "manual review" in combined.lower()
