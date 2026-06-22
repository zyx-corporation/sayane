"""Aggregated operator packaging/supervision phase status."""

from __future__ import annotations

import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from sayane.app.daemon_packaging_status import build_daemon_packaging_status
from sayane.app.daemon_recovery_consent_status import build_daemon_recovery_consent_status
from sayane.app.daemon_service_control_boundary import build_daemon_service_control_boundary
from sayane.app.daemon_service_targets_status import build_daemon_service_targets_status
from sayane.app.daemon_supervision_status import build_daemon_supervision_status


@dataclass(frozen=True)
class ResidentDaemonOperatorPhaseStatus:
    """Current aggregated post-app operator phase status."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        packaging = build_daemon_packaging_status(
            self.runtime_root,
            host=self.host,
            port=self.port,
        ).public_metadata()
        service_targets = build_daemon_service_targets_status(
            self.runtime_root,
            host=self.host,
            port=self.port,
        ).public_metadata()
        service_control = build_daemon_service_control_boundary(
            self.runtime_root,
            host=self.host,
            port=self.port,
        ).public_metadata()
        supervision = build_daemon_supervision_status(
            self.runtime_root,
            host=self.host,
            port=self.port,
        ).public_metadata()
        recovery = build_daemon_recovery_consent_status(
            self.runtime_root,
            host=self.host,
            port=self.port,
        ).public_metadata()
        startup_command = ["sayane", "serve", "--host", self.host, "--port", str(self.port)]
        return {
            "kind": "resident_daemon_operator_phase_status",
            "phase": "operator_packaging_and_supervision",
            "phase_status": "baseline_contracts_implemented_next_phase_open",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "current_supported_operator_path": {
                "startup_command": startup_command,
                "startup_command_text": " ".join(shlex.quote(part) for part in startup_command),
                "bootstrap_ui": f"http://{self.host}:{self.port}/app/ui",
                "local_only": True,
                "notes": [
                    "current supported operator path remains local Python CLI plus Local Bridge",
                    "resident app shell remains a Bridge-hosted local shell over existing app-facing endpoints",
                ],
            },
            "workstreams": [
                {
                    "name": "packaging_model_decision",
                    "status": "baseline_contract_implemented",
                    "current_state": packaging["packaging_model"],
                    "active_entrypoint": packaging["current_entrypoint"]["command_text"],
                },
                {
                    "name": "service_integration_line",
                    "status": packaging["service_integration"]["status"],
                    "current_target": service_targets.get("recommended_target"),
                    "current_platform": service_targets.get("current_platform"),
                    "allowed_service_commands": [
                        item["command"]
                        for item in service_control["service_plane"].get("allowed_commands", [])
                    ],
                    "deferred_service_commands": service_control["service_plane"].get(
                        "deferred_commands",
                        [],
                    ),
                    "lifecycle_operations": service_control["service_plane"].get(
                        "lifecycle_operations",
                        [],
                    ),
                },
                {
                    "name": "supervision_ux_line",
                    "status": supervision["active_supervision"]["status"],
                    "passive_visibility_status": supervision["passive_visibility"]["status"],
                    "background_status": supervision["background_surfaces"]["status"],
                },
                {
                    "name": "recovery_and_consent_line",
                    "status": recovery["phase_status"],
                    "consent_model": recovery["consent_model"],
                    "recovery_model": recovery["recovery_model"],
                },
            ],
            "recommended_implementation_order": [
                "packaging_model_decision",
                "supervision_ux_decision",
                "service_control_boundary_definition",
                "consent_and_recovery_alignment",
                "operator_handoff_update",
            ],
            "exit_criteria": [
                "supported operator packaging model is explicit",
                "allowed daemon control and supervision actions are explicit",
                "CLI-only actions remain explicit",
                "allowed local app UI exposure is explicit",
                "failed-supervision recovery path is explicit",
            ],
            "not_in_scope": [
                "daemon identity proof by itself",
                "daemon readiness or API readiness proof by itself",
                "direct profile patch UI",
                "replacing the current candidate review boundary",
            ],
            "read_surfaces": [
                "sayane app daemon-operator-phase-status --json",
                "sayane app daemon-packaging-status --json",
                "sayane app daemon-service-targets-status --json",
                "sayane app daemon-service-control-boundary --json",
                "sayane app daemon-supervision-status --json",
                "sayane app daemon-recovery-consent-status --json",
            ],
            "packaging_status": packaging,
            "service_targets_status": service_targets,
            "service_control_boundary": service_control,
            "supervision_status": supervision,
            "recovery_consent_status": recovery,
        }


def build_daemon_operator_phase_status(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonOperatorPhaseStatus:
    """Build the aggregated operator packaging/supervision phase status payload."""
    return ResidentDaemonOperatorPhaseStatus(runtime_root=runtime_root, host=host, port=port)
