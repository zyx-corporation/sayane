"""Resident daemon lifecycle contract model.

This module does not start a daemon. It records the intended lifecycle states
and local-only binding constraints for a future resident process.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ResidentDaemonState(StrEnum):
    """Future resident daemon lifecycle states."""

    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    FAILED = "failed"


class ResidentDaemonMode(StrEnum):
    """Daemon ownership mode."""

    BRIDGE_DELEGATION = "bridge_delegation"
    RESIDENT_SERVER_RESERVED = "resident_server_reserved"


LOCAL_BIND_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})

_ALLOWED_TRANSITIONS: dict[ResidentDaemonState, frozenset[ResidentDaemonState]] = {
    ResidentDaemonState.STOPPED: frozenset(
        {ResidentDaemonState.STARTING, ResidentDaemonState.FAILED},
    ),
    ResidentDaemonState.STARTING: frozenset(
        {ResidentDaemonState.RUNNING, ResidentDaemonState.FAILED, ResidentDaemonState.STOPPING},
    ),
    ResidentDaemonState.RUNNING: frozenset(
        {ResidentDaemonState.STOPPING, ResidentDaemonState.FAILED},
    ),
    ResidentDaemonState.STOPPING: frozenset(
        {ResidentDaemonState.STOPPED, ResidentDaemonState.FAILED},
    ),
    ResidentDaemonState.FAILED: frozenset(
        {ResidentDaemonState.STOPPED, ResidentDaemonState.STARTING},
    ),
}


def is_local_bind_host(host: str) -> bool:
    """Return True when a future resident daemon bind host is local-only."""
    return host in LOCAL_BIND_HOSTS


def validate_local_bind_host(host: str) -> None:
    """Raise when a future resident daemon bind host is not local-only."""
    if not is_local_bind_host(host):
        msg = "resident daemon lifecycle requires localhost binding"
        raise ValueError(msg)


@dataclass(frozen=True)
class ResidentDaemonLifecycle:
    """Non-running daemon lifecycle contract for future implementation."""

    state: ResidentDaemonState = ResidentDaemonState.STOPPED
    mode: ResidentDaemonMode = ResidentDaemonMode.BRIDGE_DELEGATION
    host: str = "127.0.0.1"
    port: int = 38741
    runtime_backend: str = "legacy_process_local"
    unlock_session_binding: str = "unbound"
    capability_policy: str = "local_development"
    notes: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        validate_local_bind_host(self.host)

    def can_transition_to(self, next_state: ResidentDaemonState | str) -> bool:
        """Return True when a lifecycle state transition is allowed."""
        target = ResidentDaemonState(next_state)
        return target in _ALLOWED_TRANSITIONS[self.state]

    def transition_to(
        self,
        next_state: ResidentDaemonState | str,
        *,
        note: str | None = None,
    ) -> ResidentDaemonLifecycle:
        """Return a new lifecycle contract after a valid transition."""
        target = ResidentDaemonState(next_state)
        if not self.can_transition_to(target):
            msg = f"invalid resident daemon transition: {self.state.value} -> {target.value}"
            raise ValueError(msg)
        notes = self.notes + ((note,) if note else ())
        return ResidentDaemonLifecycle(
            state=target,
            mode=self.mode,
            host=self.host,
            port=self.port,
            runtime_backend=self.runtime_backend,
            unlock_session_binding=self.unlock_session_binding,
            capability_policy=self.capability_policy,
            notes=notes,
        )

    def public_metadata(self) -> dict[str, Any]:
        """Return non-sensitive lifecycle diagnostics."""
        return {
            "state": self.state.value,
            "mode": self.mode.value,
            "host": self.host,
            "port": self.port,
            "runtime_backend": self.runtime_backend,
            "unlock_session_binding": self.unlock_session_binding,
            "capability_policy": self.capability_policy,
            "is_local_bind": is_local_bind_host(self.host),
            "notes": list(self.notes),
            "is_running_daemon": False,
        }
