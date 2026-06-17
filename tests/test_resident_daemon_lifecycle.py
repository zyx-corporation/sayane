"""Tests for resident daemon lifecycle contract (#187)."""

from __future__ import annotations

import pytest

from sayane.app.daemon_lifecycle import (
    ResidentDaemonLifecycle,
    ResidentDaemonMode,
    ResidentDaemonState,
    is_local_bind_host,
    validate_local_bind_host,
)


def test_resident_daemon_lifecycle_defaults_to_non_running_bridge_delegation() -> None:
    lifecycle = ResidentDaemonLifecycle()

    assert lifecycle.public_metadata() == {
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
    }


def test_local_bind_hosts_are_explicit() -> None:
    assert is_local_bind_host("127.0.0.1") is True
    assert is_local_bind_host("localhost") is True
    assert is_local_bind_host("::1") is True
    assert is_local_bind_host("0.0.0.0") is False

    validate_local_bind_host("localhost")
    with pytest.raises(ValueError, match="localhost"):
        validate_local_bind_host("0.0.0.0")


def test_resident_daemon_lifecycle_rejects_non_local_bind() -> None:
    with pytest.raises(ValueError, match="localhost"):
        ResidentDaemonLifecycle(host="0.0.0.0")


def test_resident_daemon_lifecycle_allows_expected_transitions() -> None:
    lifecycle = ResidentDaemonLifecycle()

    starting = lifecycle.transition_to(ResidentDaemonState.STARTING, note="operator start")
    running = starting.transition_to("running")
    stopping = running.transition_to(ResidentDaemonState.STOPPING)
    stopped = stopping.transition_to("stopped")

    assert starting.state is ResidentDaemonState.STARTING
    assert running.state is ResidentDaemonState.RUNNING
    assert stopping.state is ResidentDaemonState.STOPPING
    assert stopped.state is ResidentDaemonState.STOPPED
    assert starting.notes == ("operator start",)


def test_resident_daemon_lifecycle_rejects_invalid_transition() -> None:
    lifecycle = ResidentDaemonLifecycle(state=ResidentDaemonState.RUNNING)

    assert lifecycle.can_transition_to(ResidentDaemonState.STARTING) is False
    with pytest.raises(ValueError, match="running -> starting"):
        lifecycle.transition_to(ResidentDaemonState.STARTING)


def test_resident_daemon_lifecycle_can_restart_from_failed() -> None:
    lifecycle = ResidentDaemonLifecycle(state=ResidentDaemonState.FAILED)

    assert lifecycle.can_transition_to(ResidentDaemonState.STOPPED) is True
    assert lifecycle.can_transition_to(ResidentDaemonState.STARTING) is True


def test_resident_server_mode_is_reserved_not_running() -> None:
    lifecycle = ResidentDaemonLifecycle(
        mode=ResidentDaemonMode.RESIDENT_SERVER_RESERVED,
        runtime_backend="injected_repository_bundle",
    )

    assert lifecycle.public_metadata()["mode"] == "resident_server_reserved"
    assert lifecycle.public_metadata()["is_running_daemon"] is False
    assert lifecycle.public_metadata()["runtime_backend"] == "injected_repository_bundle"
