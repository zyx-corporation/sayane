"""Tests for resident daemon state machine schema."""

from __future__ import annotations

import json

import pytest

from sayane.app import (
    ResidentDaemonStateMachine,
    ResidentDaemonStateMachineState,
    ResidentDaemonStateMachineTransition,
    build_resident_daemon_state_machine,
)


def test_default_state_machine_is_schema_only_and_json_friendly() -> None:
    payload = build_resident_daemon_state_machine().public_metadata()

    assert payload["kind"] == "resident_daemon_state_machine"
    assert payload["initial_state"] == "stopped"
    assert payload["terminal_states"] == ["stopped", "failed"]
    assert payload["mutates_filesystem"] is False
    assert payload["controls_process"] is False
    assert payload["writes_pid_file"] is False
    assert payload["creates_socket"] is False
    assert payload["creates_runtime_directory"] is False
    assert payload["schema_only"] is True
    assert [transition["key"] for transition in payload["transitions"]] == [
        "request_start",
        "startup_succeeds",
        "request_stop",
        "stop_completes",
        "startup_fails",
        "runtime_fails",
        "recover_after_failure",
    ]
    json.dumps(payload)


def test_transition_requires_key_trigger_and_summary() -> None:
    with pytest.raises(ValueError, match="key"):
        ResidentDaemonStateMachineTransition(
            key=" ",
            from_state=ResidentDaemonStateMachineState.STOPPED,
            to_state=ResidentDaemonStateMachineState.STARTING,
            trigger="operator_start_request",
            summary="ok",
        )

    with pytest.raises(ValueError, match="trigger"):
        ResidentDaemonStateMachineTransition(
            key="request_start",
            from_state=ResidentDaemonStateMachineState.STOPPED,
            to_state=ResidentDaemonStateMachineState.STARTING,
            trigger=" ",
            summary="ok",
        )

    with pytest.raises(ValueError, match="summary"):
        ResidentDaemonStateMachineTransition(
            key="request_start",
            from_state=ResidentDaemonStateMachineState.STOPPED,
            to_state=ResidentDaemonStateMachineState.STARTING,
            trigger="operator_start_request",
            summary=" ",
        )


def test_state_machine_transition_metadata_keeps_consent_explicit() -> None:
    transition = ResidentDaemonStateMachineTransition(
        key="request_start",
        from_state=ResidentDaemonStateMachineState.STOPPED,
        to_state=ResidentDaemonStateMachineState.STARTING,
        trigger="operator_start_request",
        summary="move to starting",
        requires_operator_consent=True,
        evidence=("docs/architecture/resident-daemon-process-control-policy.md",),
    )

    assert transition.public_metadata() == {
        "key": "request_start",
        "from_state": "stopped",
        "to_state": "starting",
        "trigger": "operator_start_request",
        "summary": "move to starting",
        "requires_operator_consent": True,
        "evidence": ["docs/architecture/resident-daemon-process-control-policy.md"],
    }


def test_state_machine_can_be_constructed_with_custom_terminal_states() -> None:
    machine = ResidentDaemonStateMachine(
        initial_state=ResidentDaemonStateMachineState.STOPPED,
        terminal_states=(ResidentDaemonStateMachineState.STOPPED,),
        transitions=(),
    )

    assert machine.public_metadata()["terminal_states"] == ["stopped"]
