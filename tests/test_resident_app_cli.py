"""Tests for resident app CLI command wiring (#180/#182/#185/#188)."""

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
        "capabilities": ["admin", "capture", "mcp", "ui"],
        "repository_backend": "legacy_process_local",
        "storage_boundary": "none",
        "repository_selection": {
            "backend": "legacy_process_local",
            "has_repositories": False,
            "storage_boundary": "none",
            "notes": [
                "legacy process-local fallback only; not a production durable "
                "resident state store",
            ],
        },
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


def test_resident_app_review_queue_json_empty_default(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "review-queue", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "profile_id": "default",
        "kind": "resident_review_queue",
        "is_review_surface": True,
        "is_mcp_context": False,
        "items": [],
        "repository_available": False,
    }


def test_resident_app_mcp_preview_json_empty_default(isolated_home: Path) -> None:
    result = runner.invoke(
        app,
        ["app", "mcp-preview", "--mode", "full", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "profile_id": "default",
        "mode": "full",
        "is_derived_context": True,
        "is_canonical_profile": False,
        "included_approved_candidates": [],
        "blocked_candidates": [],
        "repository_available": False,
        "preview": {
            "kind": "resident_mcp_preview",
            "is_preview": True,
            "is_derived_context": True,
            "is_canonical_profile": False,
        },
    }


def test_resident_app_daemon_status_json(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "daemon-status", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "state": "stopped",
        "mode": "bridge_delegation",
        "host": "127.0.0.1",
        "port": 38741,
        "runtime_backend": "legacy_process_local",
        "unlock_session_binding": "unbound",
        "capability_policy": "local_development",
        "is_local_bind": True,
        "notes": [],
        "is_running_daemon": False,
        "kind": "resident_daemon_lifecycle_status",
    }


def test_resident_app_daemon_plan_json(isolated_home: Path) -> None:
    result = runner.invoke(
        app,
        ["app", "daemon-plan", "--host", "localhost", "--port", "39000", "--json"],
    )

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {
        "state": "stopped",
        "mode": "bridge_delegation",
        "host": "localhost",
        "port": 39000,
        "runtime_backend": "legacy_process_local",
        "unlock_session_binding": "unbound",
        "capability_policy": "local_development",
        "is_local_bind": True,
        "notes": [],
        "is_running_daemon": False,
        "kind": "resident_daemon_lifecycle_plan",
        "plan_only": True,
        "daemon_process_started": False,
        "resident_server_implemented": False,
        "current_serve_path": "delegate_to_sayane_serve",
        "bridge_command": ["sayane", "serve", "--host", "localhost", "--port", "39000"],
        "bridge_command_text": "sayane serve --host localhost --port 39000",
    }


def test_resident_app_daemon_commands_reject_non_localhost(isolated_home: Path) -> None:
    status = runner.invoke(app, ["app", "daemon-status", "--host", "0.0.0.0"])
    plan = runner.invoke(app, ["app", "daemon-plan", "--host", "0.0.0.0"])

    assert status.exit_code != 0
    assert plan.exit_code != 0
    assert "localhost" in (status.stdout + status.stderr + str(status.exception)).lower()
    assert "localhost" in (plan.stdout + plan.stderr + str(plan.exception)).lower()


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
        "capabilities": ["admin", "capture", "mcp", "ui"],
        "repository_backend": "legacy_process_local",
        "storage_boundary": "none",
    }


def test_resident_app_serve_rejects_non_localhost(isolated_home: Path) -> None:
    result = runner.invoke(app, ["app", "serve", "--host", "0.0.0.0"])

    assert result.exit_code != 0
    assert "localhost" in (result.stdout + result.stderr + str(result.exception)).lower()
