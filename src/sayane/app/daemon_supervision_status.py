"""Operator-facing resident daemon supervision UX status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonSupervisionStatus:
    """Current supervision UX contract for the resident daemon line."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_supervision_status",
            "supervision_mode": "passive_local_observation_with_cli_recovery",
            "phase_status": "decision_line_partially_defined",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "passive_visibility": {
                "status": "supported",
                "surfaces": [
                    "/app/overview",
                    "/app/daemon-overview",
                    "/app/screen-state/daemon",
                    "sayane app daemon-status --json",
                    "sayane app daemon-packaging-status --json",
                    "sayane app daemon-service-control-boundary --json",
                    "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
                ],
            },
            "active_supervision": {
                "status": "limited_cli_only",
                "allowed_actions": [
                    "sayane app daemon-start --json",
                    "sayane app daemon-stop --json",
                    "sayane app daemon-restart --json",
                ],
                "app_ui_actions": [],
            },
            "background_surfaces": {
                "status": "not_supported",
                "surfaces": [],
                "deferred_topics": [
                    "tray_supervision",
                    "menu_bar_supervision",
                    "login_item_or_background_agent_visibility",
                ],
            },
            "recovery_entrypoints": [
                "sayane app daemon-status --json",
                "sayane app daemon-readiness-diagnostic --operation-class bridge_health --json",
                "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
                "sayane app daemon-service-control-boundary --json",
            ],
            "ux_guardrails": [
                "passive status visibility remains separate from unrestricted daemon control",
                "current app shell does not expose tray or menu-bar supervision toggles",
                "current supervision line stays local-only and CLI-compatible",
            ],
        }


def build_daemon_supervision_status(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonSupervisionStatus:
    """Build the current supervision UX status payload."""
    return ResidentDaemonSupervisionStatus(runtime_root=runtime_root, host=host, port=port)
