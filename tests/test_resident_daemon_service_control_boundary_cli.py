"""CLI tests for resident daemon service/control boundary command."""

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


def test_daemon_service_control_boundary_json_uses_default_runtime_root(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-service-control-boundary", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["kind"] == "resident_daemon_service_control_boundary"
    assert payload["runtime_root"] == str(isolated_home / ".sayane" / "run")
    assert payload["service_plane"]["status"] in {"contract_only", "macos_explicit_cli_only"}
    assert payload["service_plane"]["lifecycle_operations"][0]["operation"] == "install"


def test_daemon_service_control_boundary_text_exposes_post_app_detail_surface(
    isolated_home: Path,
) -> None:
    result = runner.invoke(app, ["app", "daemon-service-control-boundary"])

    assert result.exit_code == 0
    assert "rollback_required: True" in result.stdout
    assert "platform_policy_required: True" in result.stdout
    assert "control_plane_allowed_commands:" in result.stdout
    assert "service_plane_allowed_commands:" in result.stdout
    assert "deferred_commands:" in result.stdout
    assert "daemon-service-install" in result.stdout
    assert "lifecycle_operations:" in result.stdout
    assert "allowed_reads:" in result.stdout
    assert "forbidden_control_exposure:" in result.stdout
