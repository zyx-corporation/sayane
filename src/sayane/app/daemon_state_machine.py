"""Schema-only resident daemon state machine.

This module defines a JSON-friendly state machine shape for a future resident
daemon. It does not start or stop processes, write PID files, create sockets,
or mutate runtime state.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResidentDaemonStateMachineState(StrEnum):
    """Schema-only resident daemon states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


@dataclass(frozen=True)
class ResidentDaemonStateMachineTransition:
    """One schema-only daemon state transition."""

    key: str
    from_state: ResidentDaemonStateMachineState
    to_state: ResidentDaemonStateMachineState
    trigger: str
    summary: str
    requires_operator_consent: bool = False
    evidence: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.key.strip():
            msg = "state machine transition key must not be empty"
            raise ValueError(msg)
        if not self.trigger.strip():
            msg = "state machine transition trigger must not be empty"
            raise ValueError(msg)
        if not self.summary.strip():
            msg = "state machine transition summary must not be empty"
            raise ValueError(msg)

    def public_metadata(self) -> dict[str, Any]:
        """Return JSON-friendly transition metadata."""
        return {
            "key": self.key,
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "trigger": self.trigger,
            "summary": self.summary,
            "requires_operator_consent": self.requires_operator_consent,
            "evidence": list(self.evidence),
        }


@dataclass(frozen=True)
class ResidentDaemonStateMachine:
    """Schema-only resident daemon state machine."""

    initial_state: ResidentDaemonStateMachineState
    transitions: tuple[ResidentDaemonStateMachineTransition, ...]
    terminal_states: tuple[ResidentDaemonStateMachineState, ...] = (
        ResidentDaemonStateMachineState.STOPPED,
        ResidentDaemonStateMachineState.FAILED,
    )
    mutates_filesystem: bool = False
    controls_process: bool = False
    writes_pid_file: bool = False
    creates_socket: bool = False
    creates_runtime_directory: bool = False

    def public_metadata(self) -> dict[str, Any]:
        """Return JSON-friendly state machine metadata."""
        return {
            "kind": "resident_daemon_state_machine",
            "initial_state": self.initial_state.value,
            "terminal_states": [state.value for state in self.terminal_states],
            "transitions": [transition.public_metadata() for transition in self.transitions],
            "mutates_filesystem": self.mutates_filesystem,
            "controls_process": self.controls_process,
            "writes_pid_file": self.writes_pid_file,
            "creates_socket": self.creates_socket,
            "creates_runtime_directory": self.creates_runtime_directory,
            "schema_only": True,
        }


def build_resident_daemon_state_machine() -> ResidentDaemonStateMachine:
    """Build the default schema-only resident daemon state machine."""
    return ResidentDaemonStateMachine(
        initial_state=ResidentDaemonStateMachineState.STOPPED,
        transitions=(
            ResidentDaemonStateMachineTransition(
                key="request_start",
                from_state=ResidentDaemonStateMachineState.STOPPED,
                to_state=ResidentDaemonStateMachineState.STARTING,
                trigger="operator_start_request",
                summary="A future daemon start request moves the machine into starting.",
                requires_operator_consent=True,
                evidence=(
                    "docs/architecture/resident-daemon-operator-runbook-and-consent-policy.md",
                    "docs/architecture/resident-daemon-process-control-policy.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="startup_succeeds",
                from_state=ResidentDaemonStateMachineState.STARTING,
                to_state=ResidentDaemonStateMachineState.RUNNING,
                trigger="readiness_confirmed",
                summary="A future readiness confirmation would move starting to running.",
                evidence=(
                    "docs/architecture/resident-daemon-readiness-and-api-readiness-policy.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="request_stop",
                from_state=ResidentDaemonStateMachineState.RUNNING,
                to_state=ResidentDaemonStateMachineState.STOPPING,
                trigger="operator_stop_request",
                summary="A future daemon stop request would move running to stopping.",
                requires_operator_consent=True,
                evidence=(
                    "docs/architecture/resident-daemon-operator-runbook-and-consent-policy.md",
                    "docs/architecture/resident-daemon-process-control-policy.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="stop_completes",
                from_state=ResidentDaemonStateMachineState.STOPPING,
                to_state=ResidentDaemonStateMachineState.STOPPED,
                trigger="shutdown_complete",
                summary="A future confirmed shutdown would move stopping to stopped.",
                evidence=(
                    "docs/architecture/resident-daemon-process-liveness-proof-policy.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="startup_fails",
                from_state=ResidentDaemonStateMachineState.STARTING,
                to_state=ResidentDaemonStateMachineState.FAILED,
                trigger="startup_failure_detected",
                summary="A future startup failure would move starting to failed.",
                evidence=(
                    "docs/architecture/resident-daemon-implementation-readiness-gate.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="runtime_fails",
                from_state=ResidentDaemonStateMachineState.RUNNING,
                to_state=ResidentDaemonStateMachineState.FAILED,
                trigger="runtime_failure_detected",
                summary="A future runtime failure would move running to failed.",
                evidence=(
                    "docs/architecture/resident-daemon-process-liveness-proof-policy.md",
                ),
            ),
            ResidentDaemonStateMachineTransition(
                key="recover_after_failure",
                from_state=ResidentDaemonStateMachineState.FAILED,
                to_state=ResidentDaemonStateMachineState.STOPPED,
                trigger="operator_reset_after_review",
                summary="A future reviewed recovery would return failed to stopped.",
                requires_operator_consent=True,
                evidence=(
                    "docs/architecture/resident-daemon-mutation-authorization-policy.md",
                ),
            ),
        ),
    )
