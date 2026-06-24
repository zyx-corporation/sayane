"""Operator-facing resident daemon recovery and consent status."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ResidentDaemonRecoveryConsentStatus:
    """Current recovery and consent contract for the resident daemon line."""

    runtime_root: Path
    host: str
    port: int

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_recovery_consent_status",
            "consent_model": "explicit_cli_confirmation_for_mutation",
            "recovery_model": "diagnose_then_operator_review_then_cli_action",
            "phase_status": "baseline_contract_implemented",
            "runtime_root": str(self.runtime_root),
            "host": self.host,
            "port": self.port,
            "non_mutating_diagnostics": [
                "sayane app daemon-status --json",
                "sayane app daemon-readiness-diagnostic --operation-class bridge_health --json",
                "sayane app daemon-proof-diagnostics --operation-class bridge_health --json",
                "sayane app daemon-packaging-status --json",
                "sayane app daemon-service-control-boundary --json",
                "sayane app daemon-supervision-status --json",
            ],
            "mutating_recovery_actions": [
                {
                    "command": "sayane app daemon-runtime-init --apply --json",
                    "consent_required": True,
                    "scope": "runtime initialization artifacts",
                },
                {
                    "command": "sayane app daemon-cleanup-apply --json",
                    "consent_required": True,
                    "scope": "reviewed local stale-artifact cleanup",
                },
                {
                    "command": "sayane app daemon-repair-apply --json",
                    "consent_required": True,
                    "scope": "reviewed local runtime directory repair",
                },
            ],
            "control_recovery_actions": [
                {
                    "command": "sayane app daemon-start --json",
                    "consent_required": False,
                    "notes": [
                        "runtime init must already be complete",
                        "manual review blocks control when runtime artifacts are ambiguous",
                    ],
                },
                {
                    "command": "sayane app daemon-stop --json",
                    "consent_required": False,
                    "notes": [
                        "bounded local process control only",
                    ],
                },
                {
                    "command": "sayane app daemon-restart --json",
                    "consent_required": False,
                    "notes": [
                        "bounded local process control only",
                    ],
                },
            ],
            "app_ui_guardrails": [
                "local app UI may expose read-only recovery guidance but "
                "not destructive consent bypasses",
                "automation must not bypass explicit operator review for cleanup or repair apply",
                "background supervision must not silently escalate into mutating recovery",
            ],
            "recommended_recovery_flow": [
                "inspect current status and proof-oriented diagnostics",
                "review stale-artifact, cleanup, repair, or runtime-init previews when needed",
                "apply only explicit CLI actions with current confirmation inputs",
                "re-check status and readiness after any local recovery step",
            ],
        }


def build_daemon_recovery_consent_status(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> ResidentDaemonRecoveryConsentStatus:
    """Build the current recovery and consent status payload."""
    return ResidentDaemonRecoveryConsentStatus(runtime_root=runtime_root, host=host, port=port)
