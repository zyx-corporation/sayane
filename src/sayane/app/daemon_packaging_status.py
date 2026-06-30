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
        native_launcher_command = ["./scripts/run-macos-app-preview.sh"]
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
        packaging_candidates = [
            {
                "model": "cli_first_local_bridge",
                "status": "current_supported_line",
                "operator_value": (
                    "lowest-change path over the existing local Bridge and resident app shell"
                ),
                "host_assumptions": [
                    "operator starts Bridge explicitly",
                    "browser shell stays local-only",
                ],
                "blocked_by": [],
            },
            {
                "model": "hybrid_local_bridge_plus_service_targets",
                "status": "candidate_requires_phase_closure",
                "operator_value": (
                    "keep Bridge-hosted local shell while adding explicit "
                    "OS service lifecycle support"
                ),
                "host_assumptions": [
                    "platform-specific service rollback policy exists",
                    "service install/update/remove semantics are explicit",
                ],
                "blocked_by": [
                    "service lifecycle implementation",
                    "platform rollback policy",
                    "operator packaging decision closure",
                ],
            },
            {
                "model": "service_first_resident_runtime",
                "status": "candidate_requires_larger_architecture_change",
                "operator_value": (
                    "daemon/service becomes the primary operator entrypoint "
                    "rather than explicit Bridge startup"
                ),
                "host_assumptions": [
                    "resident runtime service semantics replace current CLI-first startup path",
                    "supervision UX becomes a primary operator commitment",
                ],
                "blocked_by": [
                    "service lifecycle implementation",
                    "background supervision decision",
                    "auth/runtime model redesign",
                ],
            },
        ]
        return {
            "kind": "resident_daemon_packaging_status",
            "packaging_model": "cli_first_local_bridge",
            "supervision_model": "manual_cli_with_bridge_delegation",
            "phase_status": "mvp_supported_native_first_line",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "current_entrypoint": {
                "mode": "delegate_to_sayane_serve",
                "command": serve_command,
                "command_text": " ".join(shlex.quote(part) for part in serve_command),
                "purpose": "primary local operator entrypoint",
            },
            "operator_surface": {
                "primary_ui": (
                    "native_macos_app_primary"
                    if platform_family == "macos"
                    else "local_bridge_shell_primary"
                ),
                "debug_ui": "bridge_hosted_debug_shell",
                "recommended_launcher": {
                    "command": (
                        native_launcher_command if platform_family == "macos" else serve_command
                    ),
                    "command_text": (
                        " ".join(shlex.quote(part) for part in native_launcher_command)
                        if platform_family == "macos"
                        else " ".join(shlex.quote(part) for part in serve_command)
                    ),
                    "purpose": (
                        "primary native operator entrypoint"
                        if platform_family == "macos"
                        else "primary local operator entrypoint"
                    ),
                },
                "notes": [
                    (
                        "native macOS app is the primary operator-facing UI; "
                        "/app/ui remains debug-only compatibility"
                        if platform_family == "macos"
                        else (
                            "Bridge-hosted local shell remains the primary "
                            "operator-facing UI on this platform"
                        )
                    ),
                ],
            },
            "packaging_decision": {
                "status": "mvp_supported_model_finalized",
                "current_supported_model": "cli_first_local_bridge",
                "candidate_models": packaging_candidates,
                "decision_guardrails": [
                    "do not smuggle service-first commitments into MVP native-app polish",
                    "do not imply background supervision support inside MVP",
                    "keep the current local-only operator path explicit for the Community MVP",
                ],
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
                "status": (
                    "macos_launchagent_preview_apply_control"
                    if platform_family == "macos"
                    else "linux_systemd_user_preview_apply_unit_write"
                    if platform_family == "linux"
                    else "contract_only"
                ),
                "supported_targets": (
                    ["macos_launchagent"]
                    if platform_family == "macos"
                    else ["linux_systemd_user"]
                    if platform_family == "linux"
                    else []
                ),
                "reason": (
                    "Common cross-platform service targets are defined; "
                    "concrete preview/apply exists for macOS LaunchAgent and Linux systemd --user, "
                    "while explicit install/update/remove closure remains deferred."
                ),
            },
            "background_supervision": {
                "status": "not_supported",
                "supported_surfaces": [],
                "reason": (
                    "Tray, menu-bar, and background supervision UX remain separate-plan items."
                ),
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
