"""Cross-platform resident daemon service target status."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def _platform_family() -> str:
    if sys.platform == "darwin":
        return "macos"
    if sys.platform.startswith("linux"):
        return "linux"
    if sys.platform.startswith("win"):
        return "windows"
    return "other"


@dataclass(frozen=True)
class ResidentDaemonServiceTargetsStatus:
    """Current cross-platform service target status."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        current_platform = _platform_family()
        macos_status = (
            "supported_preview_apply_control" if current_platform == "macos" else "contract_only"
        )
        return {
            "kind": "resident_daemon_service_targets_status",
            "current_platform": current_platform,
            "runtime_root": str(self.runtime_root),
            "policy_gates": {
                "platform_policy_required": True,
                "rollback_policy_required": True,
                "hybrid_packaging_gate": "post_mvp_only",
            },
            "targets": [
                {
                    "target": "macos_launchagent",
                    "platform": "macos",
                    "service_manager": "launchd",
                    "status": macos_status,
                    "policy_status": "partial_preview_apply_control"
                    if current_platform == "macos"
                    else "contract_only",
                    "rollback_policy_status": "reviewed_local_control_only"
                    if current_platform == "macos"
                    else "not_defined",
                    "packaging_gate_status": "post_mvp_candidate",
                    "commands": [
                        "sayane app daemon-launchagent-preview --json",
                        "sayane app daemon-launchagent-apply --json",
                        "sayane app daemon-launchagent-bootstrap --json",
                        "sayane app daemon-launchagent-bootout --json",
                        "sayane app daemon-launchagent-kickstart --json",
                    ],
                    "blocked_by": [
                        "service lifecycle install/update/remove closure",
                        "platform rollback policy",
                    ],
                },
                {
                    "target": "linux_systemd_user",
                    "platform": "linux",
                    "service_manager": "systemd --user",
                    "status": "contract_only",
                    "commands": [],
                    "policy_status": "contract_only",
                    "rollback_policy_status": "not_defined",
                    "packaging_gate_status": "post_mvp_candidate",
                    "blocked_by": [
                        "service lifecycle implementation",
                        "platform rollback policy",
                        "operator packaging decision closure",
                    ],
                },
                {
                    "target": "windows_service",
                    "platform": "windows",
                    "service_manager": "Windows Service Control Manager",
                    "status": "contract_only",
                    "commands": [],
                    "policy_status": "contract_only",
                    "rollback_policy_status": "not_defined",
                    "packaging_gate_status": "post_mvp_candidate",
                    "blocked_by": [
                        "service lifecycle implementation",
                        "platform rollback policy",
                        "operator packaging decision closure",
                    ],
                },
            ],
            "recommended_target": "macos_launchagent" if current_platform == "macos" else None,
        }


def build_daemon_service_targets_status(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonServiceTargetsStatus:
    """Build the current cross-platform service target status."""
    return ResidentDaemonServiceTargetsStatus(runtime_root=runtime_root, host=host, port=port)
