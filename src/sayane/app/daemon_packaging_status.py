"""Operator-facing resident daemon packaging and supervision status."""

from __future__ import annotations

import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonPackagingStatus:
    """Current packaging and supervision contract for the resident daemon line."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        platform_family = (
            "macos"
            if sys.platform == "darwin"
            else "linux"
            if sys.platform.startswith("linux")
            else "windows"
            if sys.platform.startswith("win")
            else "other"
        )
        serve_command = ["sayane", "serve", "--host", self.host, "--port", str(self.port)]
        start_command = [
            "sayane",
            "app",
            "daemon-start",
            "--host",
            self.host,
            "--port",
            str(self.port),
            "--json",
        ]
        return {
            "kind": "resident_daemon_packaging_status",
            "packaging_model": "cli_first_local_bridge",
            "supervision_model": "manual_cli_with_bridge_delegation",
            "phase_status": "next_up_after_proof_phase",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "current_entrypoint": {
                "mode": "delegate_to_sayane_serve",
                "command": serve_command,
                "command_text": " ".join(shlex.quote(part) for part in serve_command),
                "purpose": "primary local operator entrypoint",
            },
            "local_daemon_control": {
                "status": "supported_local_mvp",
                "runtime_backend": "bridge_subprocess_local",
                "requires_runtime_init": True,
                "commands": [
                    "sayane app daemon-status --json",
                    " ".join(shlex.quote(part) for part in start_command),
                    f"sayane app daemon-stop --host {self.host} --port {self.port} --json",
                    f"sayane app daemon-restart --host {self.host} --port {self.port} --json",
                ],
            },
            "service_integration": {
                "status": "macos_launchagent_preview_apply_control" if platform_family == "macos" else "contract_only",
                "supported_targets": ["macos_launchagent"] if platform_family == "macos" else [],
                "reason": "Common cross-platform service targets are defined; concrete preview/apply plus explicit local launchctl control currently exists for macOS LaunchAgent only.",
            },
            "background_supervision": {
                "status": "not_supported",
                "supported_surfaces": [],
                "reason": "Tray, menu-bar, and background supervision UX remain separate-plan items.",
            },
            "operator_commitments": {
                "local_only": True,
                "review_boundary_preserved": True,
                "direct_profile_patch_ui": False,
            },
            "next_phase_topics": [
                "packaging_model_decision",
                "service_control_boundary_definition",
                "supervision_ux_decision",
                "recovery_and_consent_alignment",
            ],
        }


def build_daemon_packaging_status(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonPackagingStatus:
    """Build the current operator-facing packaging and supervision status payload."""
    return ResidentDaemonPackagingStatus(runtime_root=runtime_root, host=host, port=port)
