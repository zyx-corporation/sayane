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
        background_candidates = [
            {
                "surface": "tray_supervision",
                "status": "not_supported_in_mvp",
                "platform_scope": ["windows", "linux"],
                "operator_value": (
                    "quick passive status visibility and bounded entry into recovery commands"
                ),
                "forbidden_capabilities": [
                    "silent daemon mutation",
                    "consent bypass for cleanup or repair apply",
                ],
            },
            {
                "surface": "menu_bar_supervision",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos"],
                "operator_value": (
                    "local visibility for resident daemon state without "
                    "turning the app shell into a background controller"
                ),
                "forbidden_capabilities": [
                    "silent launchctl mutation",
                    "proof-style wording without stronger evidence",
                ],
            },
            {
                "surface": "login_item_or_background_agent_visibility",
                "status": "not_supported_in_mvp",
                "platform_scope": ["macos", "windows", "linux"],
                "operator_value": (
                    "startup visibility for the supported packaging model "
                    "after explicit policy closure"
                ),
                "forbidden_capabilities": [
                    "implicit startup enrollment",
                    "host-level persistence without rollback policy",
                ],
            },
        ]
        return {
            "kind": "resident_daemon_supervision_status",
            "supervision_mode": "passive_local_observation_with_cli_recovery",
            "phase_status": "mvp_boundary_finalized",
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
                "candidate_surfaces": background_candidates,
                "decision_guardrails": [
                    "background surfaces may add visibility but not bypass "
                    "explicit CLI-first control policy",
                    "background surfaces may not imply daemon proof, "
                    "readiness proof, or API readiness proof on their own",
                    "background surfaces are post-MVP candidates unless a later packaging decision reopens them",
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
                "candidate background surfaces remain post-MVP ideas, not current product commitments",
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
