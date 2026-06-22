"""macOS LaunchAgent preview/apply support for the resident daemon."""

from __future__ import annotations

import hashlib
import os
import plistlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.bridge.config import BridgeConfig


LAUNCHAGENT_LABEL = "com.sayane.resident.bridge"


class ResidentDaemonLaunchAgentApplyError(ValueError):
    """Structured LaunchAgent apply refusal or failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


class ResidentDaemonLaunchAgentControlError(RuntimeError):
    """Structured LaunchAgent control refusal or failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


@dataclass(frozen=True)
class ResidentDaemonLaunchAgentPlan:
    """LaunchAgent preview/apply plan."""

    runtime_root: Path
    host: str
    port: int
    sayane_home: Path
    plist_path: Path
    operation_id: str

    def plist_payload(self) -> dict[str, Any]:
        stdout_path = self.runtime_root / "log" / "launchagent.stdout.log"
        stderr_path = self.runtime_root / "log" / "launchagent.stderr.log"
        return {
            "Label": LAUNCHAGENT_LABEL,
            "ProgramArguments": [
                sys.executable,
                "-m",
                "sayane.cli.main",
                "serve",
                "--host",
                self.host,
                "--port",
                str(self.port),
            ],
            "RunAtLoad": True,
            "KeepAlive": True,
            "WorkingDirectory": str(self.sayane_home),
            "EnvironmentVariables": {
                "SAYANE_HOME": str(self.sayane_home),
            },
            "StandardOutPath": str(stdout_path),
            "StandardErrorPath": str(stderr_path),
        }

    def plist_xml(self) -> str:
        return plistlib.dumps(self.plist_payload(), fmt=plistlib.FMT_XML).decode("utf-8")

    def preview_hash(self) -> str:
        basis = {
            "plist_path": str(self.plist_path),
            "plist": self.plist_payload(),
        }
        return hashlib.sha256(repr(basis).encode("utf-8")).hexdigest()[:16]

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_launchagent_plan",
            "operation_id": self.operation_id,
            "preview_hash": self.preview_hash(),
            "label": LAUNCHAGENT_LABEL,
            "plist_path": str(self.plist_path),
            "service_manager": "launchd",
            "platform": "macos",
            "program_arguments": self.plist_payload()["ProgramArguments"],
            "stdout_path": self.plist_payload()["StandardOutPath"],
            "stderr_path": self.plist_payload()["StandardErrorPath"],
            "launchctl_commands": {
                "bootstrap": f"launchctl bootstrap gui/$(id -u) {self.plist_path}",
                "bootout": f"launchctl bootout gui/$(id -u) {self.plist_path}",
                "kickstart": f"launchctl kickstart -k gui/$(id -u)/{LAUNCHAGENT_LABEL}",
            },
            "writes_files": True,
            "loads_service": False,
            "plist_xml": self.plist_xml(),
        }


def build_launchagent_plan(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    sayane_home: Path | None = None,
    operation_id: str | None = None,
) -> ResidentDaemonLaunchAgentPlan:
    """Build a macOS LaunchAgent preview plan."""
    home = sayane_home or BridgeConfig().home
    plist_path = Path.home() / "Library" / "LaunchAgents" / f"{LAUNCHAGENT_LABEL}.plist"
    return ResidentDaemonLaunchAgentPlan(
        runtime_root=runtime_root,
        host=host,
        port=port,
        sayane_home=home,
        plist_path=plist_path,
        operation_id=operation_id or f"launchagent-{uuid4().hex[:12]}",
    )


def apply_launchagent_plan(
    plan: ResidentDaemonLaunchAgentPlan,
    *,
    confirm_operation_id: str | None = None,
    confirm_preview_hash: str | None = None,
) -> dict[str, Any]:
    """Write the LaunchAgent plist after explicit confirmation."""
    if confirm_operation_id != plan.operation_id:
        raise ResidentDaemonLaunchAgentApplyError(
            "launchagent apply requires matching operation id",
            payload={
                "kind": "resident_daemon_launchagent_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "result": "aborted",
                "applied": False,
                "failure_mode": "operation_id_mismatch",
            },
        )
    if confirm_preview_hash != plan.preview_hash():
        raise ResidentDaemonLaunchAgentApplyError(
            "launchagent apply requires matching preview hash",
            payload={
                "kind": "resident_daemon_launchagent_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "result": "aborted",
                "applied": False,
                "failure_mode": "preview_hash_mismatch",
            },
        )
    plan.plist_path.parent.mkdir(parents=True, exist_ok=True)
    plan.plist_path.write_text(plan.plist_xml(), encoding="utf-8")
    return {
        "kind": "resident_daemon_launchagent_receipt",
        "operation_id": plan.operation_id,
        "preview_hash": plan.preview_hash(),
        "label": LAUNCHAGENT_LABEL,
        "plist_path": str(plan.plist_path),
        "result": "written",
        "applied": True,
        "loads_service": False,
        "next_step": f"launchctl bootstrap gui/$(id -u) {plan.plist_path}",
    }


def run_launchagent_command(
    plan: ResidentDaemonLaunchAgentPlan,
    *,
    action: str,
) -> dict[str, Any]:
    """Run an explicit local-only launchctl command for the LaunchAgent."""
    if sys.platform != "darwin":
        raise ResidentDaemonLaunchAgentControlError(
            "launchctl control is supported on macOS only",
            payload={
                "kind": "resident_daemon_launchagent_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "label": LAUNCHAGENT_LABEL,
                "action": action,
                "platform": sys.platform,
                "result": "aborted",
                "applied": False,
                "failure_mode": "platform_not_supported",
            },
        )

    domain = f"gui/{os.getuid()}"
    if action == "bootstrap":
        command = ["launchctl", "bootstrap", domain, str(plan.plist_path)]
        requires_plist = True
    elif action == "bootout":
        command = ["launchctl", "bootout", domain, str(plan.plist_path)]
        requires_plist = True
    elif action == "kickstart":
        command = ["launchctl", "kickstart", "-k", f"{domain}/{LAUNCHAGENT_LABEL}"]
        requires_plist = False
    else:
        raise ResidentDaemonLaunchAgentControlError(
            f"unsupported launchctl action: {action}",
            payload={
                "kind": "resident_daemon_launchagent_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "label": LAUNCHAGENT_LABEL,
                "action": action,
                "platform": sys.platform,
                "result": "aborted",
                "applied": False,
                "failure_mode": "unsupported_action",
            },
        )

    if requires_plist and not plan.plist_path.is_file():
        raise ResidentDaemonLaunchAgentControlError(
            "launchctl action requires an existing LaunchAgent plist",
            payload={
                "kind": "resident_daemon_launchagent_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "label": LAUNCHAGENT_LABEL,
                "action": action,
                "platform": sys.platform,
                "plist_path": str(plan.plist_path),
                "result": "aborted",
                "applied": False,
                "failure_mode": "plist_missing",
            },
        )

    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    result = "completed" if completed.returncode == 0 else "failed"
    payload = {
        "kind": "resident_daemon_launchagent_control_receipt",
        "operation_id": plan.operation_id,
        "preview_hash": plan.preview_hash(),
        "label": LAUNCHAGENT_LABEL,
        "action": action,
        "platform": "macos",
        "plist_path": str(plan.plist_path),
        "command": command,
        "result": result,
        "applied": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise ResidentDaemonLaunchAgentControlError(
            f"launchctl {action} failed",
            payload=payload,
        )
    return payload
