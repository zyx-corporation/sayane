"""Operator-facing resident daemon service/control boundary contract."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonServiceControlBoundary:
    """Current allowed and deferred service/control boundary for operators."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        base_parts = ["--host", self.host, "--port", str(self.port), "--json"]
        start_command = ["sayane", "app", "daemon-start", *base_parts]
        stop_command = ["sayane", "app", "daemon-stop", *base_parts]
        restart_command = ["sayane", "app", "daemon-restart", *base_parts]
        return {
            "kind": "resident_daemon_service_control_boundary",
            "boundary_version": "1",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "control_plane": {
                "status": "cli_control_supported_local_mvp",
                "allowed_commands": [
                    {
                        "command": " ".join(shlex.quote(part) for part in start_command),
                        "class": "control",
                        "requires_runtime_init": True,
                        "app_ui_exposure": "next_action_only",
                    },
                    {
                        "command": " ".join(shlex.quote(part) for part in stop_command),
                        "class": "control",
                        "requires_running_process": True,
                        "app_ui_exposure": "not_exposed",
                    },
                    {
                        "command": " ".join(shlex.quote(part) for part in restart_command),
                        "class": "control",
                        "requires_runtime_init": True,
                        "app_ui_exposure": "not_exposed",
                    },
                ],
                "recovery_policy": [
                    "manual review remains required before stale-artifact cleanup or repair apply",
                    "control failures should route operators to status, log, readiness, and proof diagnostics",
                ],
            },
            "service_plane": {
                "status": "not_supported",
                "allowed_commands": [],
                "deferred_commands": [
                    "daemon-service-install",
                    "daemon-service-enable",
                    "daemon-service-disable",
                    "daemon-service-remove",
                ],
                "rollback_required": True,
                "platform_policy_required": True,
            },
            "app_ui_policy": {
                "allowed_reads": [
                    "/app/overview",
                    "/app/daemon-overview",
                    "/app/screen-state/daemon",
                ],
                "allowed_writes": [],
                "allowed_control_exposure": [
                    "daemon-start may appear as a next action when runtime is initialized and no manual review is required",
                ],
                "forbidden_control_exposure": [
                    "direct OS service install/enable/disable actions",
                    "background supervision toggles",
                    "automated bypass of consent or review boundaries",
                ],
            },
            "governing_rules": [
                "preview commands do not mutate",
                "apply commands require explicit operator consent",
                "control commands remain local-only and CLI-first in the current MVP",
                "service commands remain deferred until platform-specific rollback policy exists",
            ],
        }


def build_daemon_service_control_boundary(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonServiceControlBoundary:
    """Build the current service/control boundary contract."""
    return ResidentDaemonServiceControlBoundary(runtime_root=runtime_root, host=host, port=port)
