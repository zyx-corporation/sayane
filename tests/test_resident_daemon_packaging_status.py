"""Tests for resident daemon packaging and supervision status."""

from __future__ import annotations

from pathlib import Path

from sayane.app import build_daemon_packaging_status


def test_daemon_packaging_status_exposes_cli_first_local_boundary(tmp_path: Path) -> None:
    runtime_root = tmp_path / "run"

    payload = build_daemon_packaging_status(
        runtime_root,
        host="localhost",
        port=39000,
    ).public_metadata()

    assert payload["kind"] == "resident_daemon_packaging_status"
    assert payload["packaging_model"] == "cli_first_local_bridge"
    assert payload["supervision_model"] == "manual_cli_with_bridge_delegation"
    assert payload["service_integration"]["status"] in {"contract_only", "macos_launchagent_preview_apply"}
    assert payload["background_supervision"]["status"] == "not_supported"
    assert payload["current_entrypoint"]["command"] == [
        "sayane",
        "serve",
        "--host",
        "localhost",
        "--port",
        "39000",
    ]
    assert "sayane app daemon-start --host localhost --port 39000 --json" in payload[
        "local_daemon_control"
    ]["commands"]
