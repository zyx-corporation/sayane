"""Minimal resident UI review queue, MCP preview, and daemon overview skeleton."""

from __future__ import annotations

import sys
from dataclasses import asdict
from pathlib import Path
from typing import Any

from sayane.app.capabilities import CapabilityToken
from sayane.app.daemon_cleanup_apply import build_cleanup_apply_preview
from sayane.app.daemon_identity import ResidentDaemonIdentity
from sayane.app.daemon_launchagent import build_launchagent_plan, build_launchagent_status
from sayane.app.daemon_liveness_diagnostics import build_liveness_diagnostic
from sayane.app.daemon_packaging_status import build_daemon_packaging_status
from sayane.app.daemon_process_control import build_daemon_status_report
from sayane.app.daemon_readiness_diagnostics import build_readiness_diagnostic
from sayane.app.daemon_recovery_consent_status import build_daemon_recovery_consent_status
from sayane.app.daemon_repair_apply import build_repair_apply_preview
from sayane.app.daemon_runtime_init import build_runtime_init_plan
from sayane.app.daemon_service_control_boundary import build_daemon_service_control_boundary
from sayane.app.daemon_service_targets_status import build_daemon_service_targets_status
from sayane.app.daemon_supervision_status import build_daemon_supervision_status
from sayane.app.daemon_systemd_user import build_systemd_user_plan, build_systemd_user_status
from sayane.core.candidate import CandidateUpdate
from sayane.core.mcp_context import build_compiled_context, build_mcp_exposure_denial
from sayane.core.review_decision import ReviewDecision
from sayane.storage.repositories import RepositoryBundle


def build_review_queue(
    repositories: RepositoryBundle,
    *,
    capability: CapabilityToken,
    include_statuses: tuple[str, ...] = ("pending", "evaluated"),
    repository_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal Candidate review queue payload for resident UI.

    This is a review surface, not an MCP context export path.
    """
    capability.require("ui")
    kwargs = repository_kwargs or {}
    decisions = repositories.review_decisions.list(**kwargs)
    latest_decisions = _latest_decision_by_candidate(decisions)
    candidates = [
        candidate
        for candidate in repositories.candidates.list(**kwargs)
        if candidate.status in include_statuses
    ]
    candidates.sort(key=lambda candidate: candidate.source.captured_at.isoformat())
    return {
        "profile_id": repositories.profile_id,
        "kind": "resident_review_queue",
        "is_review_surface": True,
        "is_mcp_context": False,
        "items": [
            _candidate_to_review_item(candidate, latest_decisions.get(candidate.id))
            for candidate in candidates
        ],
    }


def build_mcp_preview(
    repositories: RepositoryBundle,
    *,
    capability: CapabilityToken,
    mode: str = "full",
    repository_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build an explicit resident UI preview of MCP compiled context.

    The preview is derived context. It must not become canonical profile state.
    Pending Candidate content remains blocked from normal context.
    """
    capability.require("mcp")
    kwargs = repository_kwargs or {}
    decisions = repositories.review_decisions.list(**kwargs)
    compiled = build_compiled_context(
        profile_id=repositories.profile_id,
        mode=mode,
        scoped_decisions=decisions,
    )
    decided_candidate_ids = {decision.candidate_id for decision in decisions}
    pending_candidates = [
        candidate
        for candidate in repositories.candidates.list(**kwargs)
        if candidate.id not in decided_candidate_ids
    ]
    for candidate in pending_candidates:
        compiled["blocked_candidates"].append(
            build_mcp_exposure_denial(
                "candidate_not_reviewed",
                candidate_id=candidate.id,
                exposure_class="pending_candidate",
            )
        )
    compiled["preview"] = {
        "kind": "resident_mcp_preview",
        "is_preview": True,
        "is_derived_context": True,
        "is_canonical_profile": False,
    }
    return compiled


def build_daemon_overview_preview(
    runtime_root: Path,
    *,
    capability: CapabilityToken,
    host: str = "127.0.0.1",
    port: int = 38741,
) -> dict[str, Any]:
    """Build a resident UI-oriented daemon overview preview payload."""
    capability.require("ui")
    status_report = build_daemon_status_report(runtime_root, host=host, port=port)
    identity = ResidentDaemonIdentity(runtime_dir=runtime_root)
    liveness = build_liveness_diagnostic(identity).public_metadata()
    readiness = build_readiness_diagnostic(
        runtime_root,
        host=host,
        port=port,
        operation_class="bridge_health",
    ).public_metadata()
    runtime_init = build_runtime_init_plan(runtime_root).public_metadata()
    cleanup_preview = build_cleanup_apply_preview(
        runtime_root,
        host=host,
        port=port,
    )
    repair_preview = build_repair_apply_preview(
        runtime_root,
        host=host,
        port=port,
    )
    packaging_status = build_daemon_packaging_status(
        runtime_root,
        host=host,
        port=port,
    ).public_metadata()
    service_control_boundary = build_daemon_service_control_boundary(
        runtime_root,
        host=host,
        port=port,
    ).public_metadata()
    service_targets_status = build_daemon_service_targets_status(
        runtime_root,
        host=host,
        port=port,
    ).public_metadata()
    supervision_status = build_daemon_supervision_status(
        runtime_root,
        host=host,
        port=port,
    ).public_metadata()
    recovery_consent_status = build_daemon_recovery_consent_status(
        runtime_root,
        host=host,
        port=port,
    ).public_metadata()
    launchagent_preview = (
        build_launchagent_plan(runtime_root, host=host, port=port).public_metadata()
        if sys.platform == "darwin"
        else None
    )
    launchagent_status = (
        build_launchagent_status(build_launchagent_plan(runtime_root, host=host, port=port))
        if sys.platform == "darwin"
        else None
    )
    systemd_user_preview = (
        build_systemd_user_plan(runtime_root, host=host, port=port).public_metadata()
        if sys.platform.startswith("linux")
        else None
    )
    systemd_user_status = (
        build_systemd_user_status(build_systemd_user_plan(runtime_root, host=host, port=port))
        if sys.platform.startswith("linux")
        else None
    )
    return {
        "kind": "resident_daemon_overview_preview",
        "is_daemon_surface": True,
        "is_preview": True,
        "is_derived_context": True,
        "runtime_root": str(runtime_root),
        "host": host,
        "port": port,
        "status": status_report.public_metadata(),
        "liveness": liveness,
        "readiness": readiness,
        "runtime_init": runtime_init,
        "cleanup_preview": cleanup_preview,
        "repair_preview": repair_preview,
        "packaging_status": packaging_status,
        "service_control_boundary": service_control_boundary,
        "service_targets_status": service_targets_status,
        "supervision_status": supervision_status,
        "recovery_consent_status": recovery_consent_status,
        "launchagent_preview": launchagent_preview,
        "launchagent_status": launchagent_status,
        "systemd_user_preview": systemd_user_preview,
        "systemd_user_status": systemd_user_status,
        "next_actions": _build_daemon_next_actions(
            status=status_report.public_metadata(),
            runtime_init=runtime_init,
            cleanup_preview=cleanup_preview,
            repair_preview=repair_preview,
            service_targets_status=service_targets_status,
            launchagent_preview=launchagent_preview,
            launchagent_status=launchagent_status,
            systemd_user_preview=systemd_user_preview,
            systemd_user_status=systemd_user_status,
        ),
    }


def _build_daemon_next_actions(
    *,
    status: dict[str, Any],
    runtime_init: dict[str, Any],
    cleanup_preview: dict[str, Any],
    repair_preview: dict[str, Any],
    service_targets_status: dict[str, Any],
    launchagent_preview: dict[str, Any] | None,
    launchagent_status: dict[str, Any] | None,
    systemd_user_preview: dict[str, Any] | None,
    systemd_user_status: dict[str, Any] | None,
) -> list[dict[str, str]]:
    actions: list[dict[str, str]] = []
    if not status["runtime_initialized"]:
        actions.append(
            {
                "command": "sayane app daemon-runtime-init --json",
                "reason": "Inspect missing runtime directories before any control action.",
            }
        )
    if status["manual_review_required"]:
        actions.append(
            {
                "command": "sayane app daemon-stale-artifacts --json",
                "reason": "Review ambiguous daemon artifacts before mutation or control.",
            }
        )
    if runtime_init["review_required"]:
        actions.append(
            {
                "command": "sayane app daemon-runtime-init --json",
                "reason": "Runtime initialization preview currently requires manual review.",
            }
        )
    cleanup_decisions = cleanup_preview.get("decision_report", {}).get("decisions", [])
    if any(decision.get("recommended_action") == "remove" for decision in cleanup_decisions):
        actions.append(
            {
                "command": "sayane app daemon-cleanup-preview --json",
                "reason": "Reviewed stale-file cleanup candidates are available.",
            }
        )
    repair_decisions = repair_preview.get("decisions", {})
    if any(decision.get("status") == "missing" for decision in repair_decisions.values()):
        actions.append(
            {
                "command": "sayane app daemon-repair-preview --json",
                "reason": "Missing runtime directories can be reviewed for explicit repair.",
            }
        )
    if (
        status["runtime_initialized"]
        and not status["is_running_daemon"]
        and not status["manual_review_required"]
    ):
        actions.append(
            {
                "command": "sayane app daemon-start --json",
                "reason": "Runtime is initialized and local daemon control is available.",
            }
        )
    actions.append(
        {
            "command": "sayane app daemon-operator-phase-status --json",
            "reason": (
                "Review the current packaging, service, supervision, and "
                "recovery phase contract before post-app operator changes."
            ),
        }
    )
    if service_targets_status.get("current_platform") == "macos":
        actions.append(
            {
                "command": "sayane app daemon-service-targets-status --json",
                "reason": (
                    "Review the current macOS, Linux, and Windows service "
                    "target contract before service-oriented control."
                ),
            }
        )
        actions.append(
            {
                "command": "sayane app daemon-launchagent-preview --json",
                "reason": (
                    "Review the LaunchAgent plist and explicit launchctl "
                    "commands for the macOS local service line."
                ),
            }
        )
        actions.append(
            {
                "command": "sayane app daemon-launchagent-status --json",
                "reason": (
                    "Observe whether the reviewed LaunchAgent plist exists "
                    "and whether launchd currently reports the label as "
                    "loaded."
                ),
            }
        )
        if launchagent_preview and Path(launchagent_preview.get("plist_path", "")).is_file():
            actions.append(
                {
                    "command": "sayane app daemon-launchagent-bootstrap --json",
                    "reason": (
                        "A reviewed LaunchAgent plist already exists and may "
                        "be bootstrapped explicitly."
                    ),
                }
            )
        if launchagent_status and launchagent_status.get("loaded") is True:
            actions.append(
                {
                    "command": "sayane app daemon-launchagent-kickstart --json",
                    "reason": (
                        "The LaunchAgent is already loaded and may be "
                        "explicitly kickstarted when the service line needs "
                        "a bounded restart."
                    ),
                }
            )
    if service_targets_status.get("current_platform") == "linux":
        actions.append(
            {
                "command": "sayane app daemon-service-targets-status --json",
                "reason": (
                    "Review the current Linux, macOS, and Windows service "
                    "target contract before service-oriented control."
                ),
            }
        )
        actions.append(
            {
                "command": "sayane app daemon-systemd-user-preview --json",
                "reason": (
                    "Review the systemd --user unit and explicit systemctl "
                    "commands for the Linux local service line."
                ),
            }
        )
        actions.append(
            {
                "command": "sayane app daemon-systemd-user-status --json",
                "reason": (
                    "Observe whether the reviewed systemd --user unit exists "
                    "and whether the local user service is active or enabled."
                ),
            }
        )
        if systemd_user_preview and Path(systemd_user_preview.get("unit_path", "")).is_file():
            actions.append(
                {
                    "command": "sayane app daemon-systemd-user-daemon-reload --json",
                    "reason": (
                        "A reviewed systemd --user unit already exists and the "
                        "next explicit operator step is daemon-reload."
                    ),
                }
            )
        if systemd_user_status and (
            systemd_user_status.get("enabled") is False
            or systemd_user_status.get("active") is False
        ):
            actions.append(
                {
                    "command": "sayane app daemon-systemd-user-enable-now --json",
                    "reason": (
                        "The reviewed systemd --user unit is not fully enabled "
                        "or active and can be explicitly enabled now."
                    ),
                }
            )
        if systemd_user_status and systemd_user_status.get("unit_exists") is True:
            actions.append(
                {
                    "command": "sayane app daemon-systemd-user-status --json",
                    "reason": (
                        "The reviewed systemd --user unit exists and can be "
                        "verified directly through the local CLI status surface."
                    ),
                }
            )
    if status["is_running_daemon"]:
        actions.append(
            {
                "command": "sayane app daemon-readiness-diagnostic --json",
                "reason": "Observe bounded readiness signals for the running local daemon.",
            }
        )
    if not actions:
        actions.append(
            {
                "command": "sayane app daemon-status --json",
                "reason": "Current daemon state is stable; refresh status when needed.",
            }
        )
    return actions


def _latest_decision_by_candidate(
    decisions: list[ReviewDecision],
) -> dict[str, ReviewDecision]:
    latest: dict[str, ReviewDecision] = {}
    for decision in decisions:
        latest[decision.candidate_id] = decision
    return latest


def _candidate_to_review_item(
    candidate: CandidateUpdate,
    decision: ReviewDecision | None,
) -> dict[str, Any]:
    return {
        "candidate_id": candidate.id,
        "status": candidate.status,
        "evaluation_status": candidate.evaluation_status,
        "target_profile_id": candidate.target_profile_id,
        "source_type": candidate.source.type,
        "captured_at": candidate.source.captured_at.isoformat(),
        "proposal_section": candidate.proposal.section,
        "proposal_operation": candidate.proposal.operation,
        "display_summary": candidate.display_summary or candidate.proposal.summary,
        "capture_source": (
            candidate.capture_meta.capture_source if candidate.capture_meta is not None else None
        ),
        "requires_review": (
            candidate.capture_meta.requires_review if candidate.capture_meta is not None else False
        ),
        "latest_decision": asdict(decision) if decision is not None else None,
    }
