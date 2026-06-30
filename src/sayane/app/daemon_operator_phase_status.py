"""Aggregated operator packaging/supervision phase status."""

from __future__ import annotations

import shlex
import sys
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
        startup_command = (
            ["./scripts/run-macos-app-preview.sh"]
            if sys.platform == "darwin"
            else ["sayane", "serve", "--host", self.host, "--port", str(self.port)]
        )
        phase_closure_checklist = [
            {
                "item": "supported_packaging_model_finalized",
                "status": "complete",
                "blocking_reasons": [],
            },
            {
                "item": "service_lifecycle_implementation_closed",
                "status": "complete",
                "blocking_reasons": [],
            },
            {
                "item": "platform_policy_and_rollback_closed",
                "status": "complete",
                "blocking_reasons": [],
            },
            {
                "item": "background_supervision_direction_decided",
                "status": "complete",
                "blocking_reasons": [],
            },
            {
                "item": "recovery_and_consent_path_remains_explicit_under_next_model",
                "status": "complete",
                "blocking_reasons": [],
            },
        ]
        blocking_reasons = sorted(
            {
                reason
                for item in phase_closure_checklist
                for reason in item.get("blocking_reasons", [])
            }
        )
        return {
            "kind": "resident_daemon_operator_phase_status",
            "phase": "operator_packaging_and_supervision",
            "phase_status": "mvp_operator_boundary_closed",
            "phase_readiness": "ready_for_mvp_release_closure",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "current_supported_operator_path": {
                "startup_command": startup_command,
                "startup_command_text": " ".join(shlex.quote(part) for part in startup_command),
                "debug_shell_bootstrap_ui": f"http://{self.host}:{self.port}/app/ui",
                "bootstrap_ui": f"http://{self.host}:{self.port}/app/ui",
                "local_only": True,
                "primary_operator_ui": packaging["operator_surface"].get("primary_ui"),
                "debug_operator_ui": packaging["operator_surface"].get("debug_ui"),
                "recommended_launcher": packaging["operator_surface"]
                .get("recommended_launcher", {})
                .get("command_text"),
                "notes": [
                    "native macOS app is the primary MVP operator path on macOS",
                    "current supported packaging model remains local-only CLI plus Local Bridge",
                    "Bridge-hosted /app/ui remains a maintainer/debug compatibility surface",
                ],
            },
            "workstreams": [
                {
                    "name": "packaging_model_decision",
                    "status": "closed_for_mvp",
                    "current_state": packaging["packaging_model"],
                    "active_entrypoint": packaging["current_entrypoint"]["command_text"],
                    "candidate_models": packaging["packaging_decision"].get(
                        "candidate_models",
                        [],
                    ),
                },
                {
                    "name": "service_integration_line",
                    "status": "closed_for_mvp",
                    "current_target": service_targets.get("recommended_target"),
                    "current_platform": service_targets.get("current_platform"),
                    "policy_gates": service_targets.get("policy_gates", {}),
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
                    "status": "closed_for_mvp",
                    "passive_visibility_status": supervision["passive_visibility"]["status"],
                    "background_status": supervision["background_surfaces"]["status"],
                    "background_candidates": supervision["background_surfaces"].get(
                        "candidate_surfaces",
                        [],
                    ),
                },
                {
                    "name": "recovery_and_consent_line",
                    "status": "closed_for_mvp",
                    "consent_model": recovery["consent_model"],
                    "recovery_model": recovery["recovery_model"],
                },
            ],
            "recommended_implementation_order": [],
            "decision_assist": [
                {
                    "topic": "packaging_model_decision",
                    "summary": (
                        "confirm the current MVP packaging line and native-first startup path"
                    ),
                    "command": "./scripts/run-macos-app-preview.sh"
                    if sys.platform == "darwin"
                    else "sayane app daemon-packaging-status --json",
                },
                {
                    "topic": "service_control_boundary_definition",
                    "summary": (
                        "review the finalized MVP boundary before any post-MVP "
                        "service lifecycle expansion"
                    ),
                    "command": "sayane app daemon-service-control-boundary --json",
                },
                {
                    "topic": "supervision_ux_decision",
                    "summary": ("verify that MVP supervision stays passive and local-only"),
                    "command": "sayane app daemon-supervision-status --json",
                },
                {
                    "topic": "consent_and_recovery_alignment",
                    "summary": (
                        "verify that mutating recovery remains explicit CLI confirmation only"
                    ),
                    "command": "sayane app daemon-recovery-consent-status --json",
                },
            ],
            "phase_closure_checklist": phase_closure_checklist,
            "blocking_reasons": blocking_reasons,
            "closure_evidence": [
                {
                    "surface": "operator_phase_status",
                    "command": "sayane app daemon-operator-phase-status --json",
                    "confirms": "current phase readiness, blocking reasons, and closure checklist",
                },
                {
                    "surface": "packaging_status",
                    "command": "sayane app daemon-packaging-status --json",
                    "confirms": (
                        "current supported model, candidate models, and operator launcher guidance"
                    ),
                },
                {
                    "surface": "service_targets_status",
                    "command": "sayane app daemon-service-targets-status --json",
                    "confirms": "platform targets, rollback policy gate, and hybrid packaging gate",
                },
                {
                    "surface": "service_control_boundary",
                    "command": "sayane app daemon-service-control-boundary --json",
                    "confirms": (
                        "allowed local control path, deferred commands, and lifecycle operations"
                    ),
                },
                {
                    "surface": "supervision_status",
                    "command": "sayane app daemon-supervision-status --json",
                    "confirms": "background candidate surfaces and deferred supervision topics",
                },
                {
                    "surface": "recovery_consent_status",
                    "command": "sayane app daemon-recovery-consent-status --json",
                    "confirms": "mutating recovery consent requirements and recovery guardrails",
                },
            ],
            "exit_criteria": [
                "supported operator packaging model is explicit",
                "allowed daemon control and supervision actions are explicit",
                "CLI-only actions remain explicit",
                "allowed local app UI exposure is explicit",
                "failed-supervision recovery path is explicit",
                "native macOS app covers the sustained MVP operator workflow",
                "clipboard capture is available from the native app path",
            ],
            "not_in_scope": [
                "daemon identity proof by itself",
                "daemon readiness or API readiness proof by itself",
                "direct profile patch UI",
                "replacing the current candidate review boundary",
                "background supervision shipment",
                "cross-platform service packaging parity",
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
