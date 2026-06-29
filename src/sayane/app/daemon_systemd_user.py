"""Linux systemd --user preview/apply support for the resident daemon."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from uuid import uuid4

from sayane.bridge.config import BridgeConfig

SYSTEMD_USER_UNIT_NAME = "sayane-resident-bridge.service"


class ResidentDaemonSystemdUserApplyError(ValueError):
    """Structured systemd --user apply refusal or failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


class ResidentDaemonSystemdUserControlError(RuntimeError):
    """Structured systemd --user control refusal or failure."""

    def __init__(self, message: str, *, payload: dict[str, Any]) -> None:
        super().__init__(message)
        self.payload = payload


@dataclass(frozen=True)
class ResidentDaemonSystemdUserPlan:
    """systemd --user preview/apply plan."""

    runtime_root: Path
    host: str
    port: int
    sayane_home: Path
    unit_path: Path
    operation_id: str

    def unit_text(self) -> str:
        stdout_path = self.runtime_root / "log" / "systemd-user.stdout.log"
        stderr_path = self.runtime_root / "log" / "systemd-user.stderr.log"
        return "\n".join(
            [
                "[Unit]",
                "Description=Sayane Resident Bridge",
                "After=default.target",
                "",
                "[Service]",
                "Type=simple",
                f"WorkingDirectory={self.sayane_home}",
                f"Environment=SAYANE_HOME={self.sayane_home}",
                (
                    "ExecStart="
                    f"{sys.executable} -m sayane.cli.main serve --host {self.host} --port {self.port}"
                ),
                "Restart=on-failure",
                "RestartSec=3",
                f"StandardOutput=append:{stdout_path}",
                f"StandardError=append:{stderr_path}",
                "",
                "[Install]",
                "WantedBy=default.target",
                "",
            ]
        )

    def preview_hash(self) -> str:
        basis = {
            "unit_path": str(self.unit_path),
            "unit_text": self.unit_text(),
        }
        return hashlib.sha256(repr(basis).encode("utf-8")).hexdigest()[:16]

    def public_metadata(self) -> dict[str, Any]:
        return {
            "kind": "resident_daemon_systemd_user_plan",
            "operation_id": self.operation_id,
            "preview_hash": self.preview_hash(),
            "unit_name": SYSTEMD_USER_UNIT_NAME,
            "unit_path": str(self.unit_path),
            "service_manager": "systemd --user",
            "platform": "linux",
            "program_arguments": [
                sys.executable,
                "-m",
                "sayane.cli.main",
                "serve",
                "--host",
                self.host,
                "--port",
                str(self.port),
            ],
            "stdout_path": str(self.runtime_root / "log" / "systemd-user.stdout.log"),
            "stderr_path": str(self.runtime_root / "log" / "systemd-user.stderr.log"),
            "systemctl_commands": {
                "daemon_reload": "systemctl --user daemon-reload",
                "enable_now": f"systemctl --user enable --now {SYSTEMD_USER_UNIT_NAME}",
                "disable_now": f"systemctl --user disable --now {SYSTEMD_USER_UNIT_NAME}",
                "status": f"systemctl --user status {SYSTEMD_USER_UNIT_NAME} --no-pager --full",
            },
            "writes_files": True,
            "loads_service": False,
            "unit_text": self.unit_text(),
        }


def build_systemd_user_plan(
    runtime_root: Path,
    *,
    host: str = "127.0.0.1",
    port: int = 38741,
    sayane_home: Path | None = None,
    operation_id: str | None = None,
) -> ResidentDaemonSystemdUserPlan:
    """Build a Linux systemd --user preview plan."""
    home = sayane_home or BridgeConfig().home
    unit_path = Path.home() / ".config" / "systemd" / "user" / SYSTEMD_USER_UNIT_NAME
    return ResidentDaemonSystemdUserPlan(
        runtime_root=runtime_root,
        host=host,
        port=port,
        sayane_home=home,
        unit_path=unit_path,
        operation_id=operation_id or f"systemd-user-{uuid4().hex[:12]}",
    )


def apply_systemd_user_plan(
    plan: ResidentDaemonSystemdUserPlan,
    *,
    confirm_operation_id: str | None = None,
    confirm_preview_hash: str | None = None,
) -> dict[str, Any]:
    """Write the systemd --user unit after explicit confirmation."""
    if confirm_operation_id != plan.operation_id:
        raise ResidentDaemonSystemdUserApplyError(
            "systemd user apply requires matching operation id",
            payload={
                "kind": "resident_daemon_systemd_user_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "result": "aborted",
                "applied": False,
                "failure_mode": "operation_id_mismatch",
            },
        )
    if confirm_preview_hash != plan.preview_hash():
        raise ResidentDaemonSystemdUserApplyError(
            "systemd user apply requires matching preview hash",
            payload={
                "kind": "resident_daemon_systemd_user_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "result": "aborted",
                "applied": False,
                "failure_mode": "preview_hash_mismatch",
            },
        )
    plan.unit_path.parent.mkdir(parents=True, exist_ok=True)
    plan.unit_path.write_text(plan.unit_text(), encoding="utf-8")
    return {
        "kind": "resident_daemon_systemd_user_receipt",
        "operation_id": plan.operation_id,
        "preview_hash": plan.preview_hash(),
        "unit_name": SYSTEMD_USER_UNIT_NAME,
        "unit_path": str(plan.unit_path),
        "result": "written",
        "applied": True,
        "loads_service": False,
        "next_steps": [
            "systemctl --user daemon-reload",
            f"systemctl --user enable --now {SYSTEMD_USER_UNIT_NAME}",
        ],
    }


def build_systemd_user_status(
    plan: ResidentDaemonSystemdUserPlan,
) -> dict[str, Any]:
    """Build a conservative Linux systemd --user status observation."""
    unit_exists = plan.unit_path.is_file()
    payload: dict[str, Any] = {
        "kind": "resident_daemon_systemd_user_status",
        "operation_id": plan.operation_id,
        "preview_hash": plan.preview_hash(),
        "unit_name": SYSTEMD_USER_UNIT_NAME,
        "platform": "linux" if sys.platform.startswith("linux") else sys.platform,
        "unit_path": str(plan.unit_path),
        "unit_exists": unit_exists,
        "service_manager": "systemd --user",
        "active_status": "unsupported_platform" if not sys.platform.startswith("linux") else "unknown",
        "enabled_status": "unsupported_platform" if not sys.platform.startswith("linux") else "unknown",
        "active": False,
        "enabled": False,
        "status_command": f"systemctl --user status {SYSTEMD_USER_UNIT_NAME} --no-pager --full",
    }
    if not sys.platform.startswith("linux"):
        return payload

    active_command = ["systemctl", "--user", "is-active", SYSTEMD_USER_UNIT_NAME]
    enabled_command = ["systemctl", "--user", "is-enabled", SYSTEMD_USER_UNIT_NAME]
    try:
        active_completed = subprocess.run(active_command, capture_output=True, text=True, check=False)
        enabled_completed = subprocess.run(enabled_command, capture_output=True, text=True, check=False)
    except FileNotFoundError:
        payload.update(
            {
                "active_status": "systemctl_not_available",
                "enabled_status": "systemctl_not_available",
                "active": False,
                "enabled": False,
                "failure_mode": "systemctl_not_available",
            }
        )
        return payload
    active_stdout = active_completed.stdout.strip()
    enabled_stdout = enabled_completed.stdout.strip()
    payload.update(
        {
            "active_command": active_command,
            "enabled_command": enabled_command,
            "active_returncode": active_completed.returncode,
            "enabled_returncode": enabled_completed.returncode,
            "active_stdout": active_stdout,
            "active_stderr": active_completed.stderr,
            "enabled_stdout": enabled_stdout,
            "enabled_stderr": enabled_completed.stderr,
            "active_status": active_stdout or "inactive",
            "enabled_status": enabled_stdout or "disabled",
            "active": active_completed.returncode == 0 and active_stdout == "active",
            "enabled": enabled_completed.returncode == 0 and enabled_stdout == "enabled",
        }
    )
    return payload


def run_systemd_user_command(
    plan: ResidentDaemonSystemdUserPlan,
    *,
    action: str,
) -> dict[str, Any]:
    """Run an explicit local-only systemd --user command for the resident unit."""
    if not sys.platform.startswith("linux"):
        raise ResidentDaemonSystemdUserControlError(
            "systemd --user control is supported on Linux only",
            payload={
                "kind": "resident_daemon_systemd_user_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "unit_name": SYSTEMD_USER_UNIT_NAME,
                "action": action,
                "platform": sys.platform,
                "result": "aborted",
                "applied": False,
                "failure_mode": "platform_not_supported",
            },
        )

    if action == "daemon_reload":
        command = ["systemctl", "--user", "daemon-reload"]
        requires_unit = False
    elif action == "enable_now":
        command = ["systemctl", "--user", "enable", "--now", SYSTEMD_USER_UNIT_NAME]
        requires_unit = True
    elif action == "disable_now":
        command = ["systemctl", "--user", "disable", "--now", SYSTEMD_USER_UNIT_NAME]
        requires_unit = True
    else:
        raise ResidentDaemonSystemdUserControlError(
            f"unsupported systemd --user action: {action}",
            payload={
                "kind": "resident_daemon_systemd_user_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "unit_name": SYSTEMD_USER_UNIT_NAME,
                "action": action,
                "platform": sys.platform,
                "result": "aborted",
                "applied": False,
                "failure_mode": "unsupported_action",
            },
        )

    if requires_unit and not plan.unit_path.is_file():
        raise ResidentDaemonSystemdUserControlError(
            "systemd --user action requires an existing unit file",
            payload={
                "kind": "resident_daemon_systemd_user_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "unit_name": SYSTEMD_USER_UNIT_NAME,
                "action": action,
                "platform": "linux",
                "unit_path": str(plan.unit_path),
                "result": "aborted",
                "applied": False,
                "failure_mode": "unit_missing",
            },
        )

    try:
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        raise ResidentDaemonSystemdUserControlError(
            "systemctl is not available on this host",
            payload={
                "kind": "resident_daemon_systemd_user_control_receipt",
                "operation_id": plan.operation_id,
                "preview_hash": plan.preview_hash(),
                "unit_name": SYSTEMD_USER_UNIT_NAME,
                "action": action,
                "platform": "linux",
                "unit_path": str(plan.unit_path),
                "command": command,
                "result": "aborted",
                "applied": False,
                "failure_mode": "systemctl_not_available",
            },
        ) from exc

    result = "completed" if completed.returncode == 0 else "failed"
    payload = {
        "kind": "resident_daemon_systemd_user_control_receipt",
        "operation_id": plan.operation_id,
        "preview_hash": plan.preview_hash(),
        "unit_name": SYSTEMD_USER_UNIT_NAME,
        "action": action,
        "platform": "linux",
        "unit_path": str(plan.unit_path),
        "command": command,
        "result": result,
        "applied": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        raise ResidentDaemonSystemdUserControlError(
            f"systemctl --user {action} failed",
            payload=payload,
        )
    return payload
