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
        phase_closure_checklist = [
            {
                "item": "supported_packaging_model_finalized",
                "status": "in_progress",
                "blocking_reasons": [
                    "hybrid and service-first candidates remain explicitly open",
                ],
            },
            {
                "item": "service_lifecycle_implementation_closed",
                "status": "blocked",
                "blocking_reasons": service_control["service_plane"].get("deferred_commands", []),
            },
            {
                "item": "platform_policy_and_rollback_closed",
                "status": "blocked",
                "blocking_reasons": [
                    service_targets["policy_gates"]["hybrid_packaging_gate"],
                ],
            },
            {
                "item": "background_supervision_direction_decided",
                "status": "in_progress",
                "blocking_reasons": [
                    item["surface"]
                    for item in supervision["background_surfaces"].get("candidate_surfaces", [])
                ],
            },
            {
                "item": "recovery_and_consent_path_remains_explicit_under_next_model",
                "status": "baseline_ready",
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
            "phase_status": "baseline_contracts_implemented_next_phase_open",
            "phase_readiness": "not_ready_for_phase_closure",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "current_supported_operator_path": {
                "startup_command": startup_command,
                "startup_command_text": " ".join(shlex.quote(part) for part in startup_command),
                "bootstrap_ui": f"http://{self.host}:{self.port}/app/ui",
                "local_only": True,
                "primary_operator_ui": packaging["operator_surface"].get("primary_ui"),
                "debug_operator_ui": packaging["operator_surface"].get("debug_ui"),
                "recommended_launcher": packaging["operator_surface"]
                .get("recommended_launcher", {})
                .get("command_text"),
                "notes": [
                    "current supported operator path remains local Python CLI plus Local Bridge",
                    "resident app shell remains a Bridge-hosted local shell "
                    "over existing app-facing endpoints",
                ],
            },
            "workstreams": [
                {
                    "name": "packaging_model_decision",
                    "status": "baseline_contract_implemented",
                    "current_state": packaging["packaging_model"],
                    "active_entrypoint": packaging["current_entrypoint"]["command_text"],
                    "candidate_models": packaging["packaging_decision"].get(
                        "candidate_models",
                        [],
                    ),
                },
                {
                    "name": "service_integration_line",
                    "status": packaging["service_integration"]["status"],
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
                    "status": supervision["active_supervision"]["status"],
                    "passive_visibility_status": supervision["passive_visibility"]["status"],
                    "background_status": supervision["background_surfaces"]["status"],
                    "background_candidates": supervision["background_surfaces"].get(
                        "candidate_surfaces",
                        [],
                    ),
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
            "decision_assist": [
                {
                    "topic": "packaging_model_decision",
                    "summary": (
                        "keep cli_first_local_bridge explicit until service lifecycle and "
                        "background supervision become intentional commitments"
                    ),
                    "command": "sayane app daemon-packaging-status --json",
                },
                {
                    "topic": "service_control_boundary_definition",
                    "summary": (
                        "close lifecycle, rollback, and platform policy before treating "
                        "service-backed startup as a supported operator path"
                    ),
                    "command": "sayane app daemon-service-control-boundary --json",
                },
                {
                    "topic": "supervision_ux_decision",
                    "summary": (
                        "decide whether background visibility stays deferred or becomes "
                        "a committed operator-facing surface"
                    ),
                    "command": "sayane app daemon-supervision-status --json",
                },
                {
                    "topic": "consent_and_recovery_alignment",
                    "summary": (
                        "keep recovery actions read-guided and consent-bound under any "
                        "next packaging model"
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
                    "confirms": "current supported model, candidate models, and operator launcher guidance",
                },
                {
                    "surface": "service_targets_status",
                    "command": "sayane app daemon-service-targets-status --json",
                    "confirms": "platform targets, rollback policy gate, and hybrid packaging gate",
                },
                {
                    "surface": "service_control_boundary",
                    "command": "sayane app daemon-service-control-boundary --json",
                    "confirms": "allowed local control path, deferred commands, and lifecycle operations",
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
