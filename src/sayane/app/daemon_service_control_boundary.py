"""Operator-facing resident daemon service/control boundary contract."""

from __future__ import annotations

import shlex
import sys
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
        launchagent_commands = [
            {
                "command": "sayane app daemon-launchagent-bootstrap --json",
                "class": "service_control",
                "platform": "macos",
                "requires_existing_plist": True,
                "app_ui_exposure": "not_exposed",
            },
            {
                "command": "sayane app daemon-launchagent-bootout --json",
                "class": "service_control",
                "platform": "macos",
                "requires_existing_plist": True,
                "app_ui_exposure": "not_exposed",
            },
            {
                "command": "sayane app daemon-launchagent-kickstart --json",
                "class": "service_control",
                "platform": "macos",
                "requires_existing_plist": False,
                "app_ui_exposure": "not_exposed",
            },
        ]
        is_macos = sys.platform == "darwin"
        lifecycle_operations = [
            {
                "operation": "install",
                "command": "daemon-service-install",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos_launchagent", "linux_systemd_user", "windows_service"],
                "rollback_required": True,
                "policy_required": True,
            },
            {
                "operation": "enable",
                "command": "daemon-service-enable",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos_launchagent", "linux_systemd_user", "windows_service"],
                "rollback_required": True,
                "policy_required": True,
            },
            {
                "operation": "disable",
                "command": "daemon-service-disable",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos_launchagent", "linux_systemd_user", "windows_service"],
                "rollback_required": True,
                "policy_required": True,
            },
            {
                "operation": "remove",
                "command": "daemon-service-remove",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos_launchagent", "linux_systemd_user", "windows_service"],
                "rollback_required": True,
                "policy_required": True,
            },
            {
                "operation": "update",
                "command": "daemon-service-update",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos_launchagent", "linux_systemd_user", "windows_service"],
                "rollback_required": True,
                "policy_required": True,
            },
        ]
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
                    "control failures should route operators to status, log, "
                    "readiness, and proof diagnostics",
                ],
            },
            "service_plane": {
                "status": "mvp_macos_launchagent_preview_apply_cli_only"
                if is_macos
                else "mvp_contract_only_non_macos",
                "allowed_commands": launchagent_commands if is_macos else [],
                "deferred_commands": [
                    "daemon-service-install",
                    "daemon-service-enable",
                    "daemon-service-disable",
                    "daemon-service-remove",
                    "daemon-service-update",
                ],
                "lifecycle_operations": lifecycle_operations,
                "platform_targets": [
                    "macos_launchagent",
                    "linux_systemd_user",
                    "windows_service",
                ],
                "rollback_required": True,
                "platform_policy_required": True,
                "update_strategy": "not_supported_in_mvp",
            },
            "app_ui_policy": {
                "allowed_reads": [
                    "/app/overview",
                    "/app/daemon-overview",
                    "/app/screen-state/daemon",
                ],
                "allowed_writes": [],
                "allowed_control_exposure": [
                    "daemon-start may appear as a next action when runtime "
                    "is initialized and no manual review is required",
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
                "macOS LaunchAgent preview/apply/bootstrap/bootout/kickstart are the only MVP service-adjacent operator path",
                "service install/enable/disable/remove/update are outside the MVP support boundary",
                (
                    "cross-platform service lifecycle and rollback-policy closure "
                    "move to post-MVP operator packaging work"
                ),
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
