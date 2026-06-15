"""Tests for resident app CLI command wiring (#180/#182)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from sayane.bridge.config import BridgeConfig
from sayane.cli.main import app
from sayane.storage.candidates import load_candidate

runner = CliRunner()


@pytest.fixture
def isolated_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    return home


def test_resident_app_status_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "profile_id": "default",
        "has_repositories": False,
        "candidate_repository": False,
        "review_decision_repository": False,
        "lineage_repository": False,
        "bridge_host": "127.0.0.1",
        "bridge_port": 38741,
        "capabilities": ["admin", "capture"],
    }


def test_resident_app_capture_clipboard_creates_candidate(isolated_home: Path) -> None:
    result = runner.invoke(
        app,
        [
            "app",
            "capture-clipboard",
            "--text",
            "important_terms:\n  - \"Sayane\"",
            "--json",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "pending"
    assert payload["source"]["type"] == "clipboard"
    assert payload["capture_meta"]["capture_source"] == "clipboard"

    config = BridgeConfig(home=isolated_home / ".sayane")
    candidate = load_candidate(config, payload["id"])
    assert candidate.status == "pending"
    assert candidate.source.type == "clipboard"
    assert candidate.capture_meta is not None
    assert candidate.capture_meta.capture_source == "clipboard"


def test_resident_app_capture_clipboard_rejects_empty_input(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "capture-clipboard", "--text", "   "])

    assert result.exit_code != 0
    assert "empty" in (result.stdout + result.stderr + str(result.exception)).lower()


def test_resident_app_serve_json_delegates_to_existing_bridge_command(
    isolated_home: Path,
) -> None:
    result = runner.invoke(
        app,
        ["app", "serve", "--host", "127.0.0.1", "--port", "39000", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "mode": "delegate_to_sayane_serve",
        "command": ["sayane", "serve", "--host", "127.0.0.1", "--port", "39000"],
        "command_text": "sayane serve --host 127.0.0.1 --port 39000",
        "bridge_host": "127.0.0.1",
        "bridge_port": 39000,
        "profile_id": "default",
        "capabilities": ["admin", "capture"],
    }


def test_resident_app_serve_rejects_non_localhost(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "serve", "--host", "0.0.0.0"])

    assert result.exit_code != 0
    assert "localhost" in (result.stdout + result.stderr + str(result.exception)).lower()
