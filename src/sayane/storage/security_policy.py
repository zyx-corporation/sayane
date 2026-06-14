"""Phase 4 storage security policy.

This module defines the minimum storage boundary before RDE/Candidate Review
creates high-sensitivity records such as Candidate, ReviewDecision, and Lineage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

SensitiveRecordClass = Literal[
    "candidate",
    "review_decision",
    "lineage",
    "raw_capture",
    "profile",
    "project_context",
]

_EXTERNAL_STORAGE_MARKERS = {
    ".git",
    ".obsidian",
    "Dropbox",
    "Google Drive",
    "OneDrive",
    "iCloud Drive",
    "Syncthing",
}


@dataclass(frozen=True)
class StorageSecurityDecision:
    """Decision for whether a storage path is acceptable for sensitive records."""

    allowed: bool
    reason: str
    path: str
    record_class: str


@dataclass(frozen=True)
class StorageSecurityPolicy:
    """Conservative local FileSystem policy until Local Vault is available."""

    allow_external_sync: bool = False
    allow_git_worktree: bool = False
    allow_obsidian_vault: bool = False

    def evaluate_path(
        self,
        path: Path,
        *,
        record_class: SensitiveRecordClass,
    ) -> StorageSecurityDecision:
        resolved = path.expanduser().resolve()
        markers = _find_external_markers(resolved)

        if ".git" in markers and not self.allow_git_worktree:
            return StorageSecurityDecision(
                allowed=False,
                reason="git_worktree_on_hold",
                path=str(resolved),
                record_class=record_class,
            )

        if ".obsidian" in markers and not self.allow_obsidian_vault:
            return StorageSecurityDecision(
                allowed=False,
                reason="obsidian_vault_on_hold",
                path=str(resolved),
                record_class=record_class,
            )

        sync_markers = markers - {".git", ".obsidian"}
        if sync_markers and not self.allow_external_sync:
            return StorageSecurityDecision(
                allowed=False,
                reason="external_sync_on_hold",
                path=str(resolved),
                record_class=record_class,
            )

        return StorageSecurityDecision(
            allowed=True,
            reason="local_filesystem_allowed",
            path=str(resolved),
            record_class=record_class,
        )


def default_storage_security_policy() -> StorageSecurityPolicy:
    """Return the default Phase 4 storage policy.

    External sync, Git worktrees, and Obsidian vaults are held until the Local
    Vault security model is implemented.
    """
    return StorageSecurityPolicy()


def require_local_working_store(
    path: Path,
    *,
    record_class: SensitiveRecordClass,
    policy: StorageSecurityPolicy | None = None,
) -> StorageSecurityDecision:
    """Require that sensitive records stay inside a local working store."""
    active_policy = policy or default_storage_security_policy()
    decision = active_policy.evaluate_path(path, record_class=record_class)
    if not decision.allowed:
        raise StorageSecurityError(decision)
    return decision


class StorageSecurityError(RuntimeError):
    """Raised when a sensitive record would be stored in a held location."""

    def __init__(self, decision: StorageSecurityDecision) -> None:
        self.decision = decision
        super().__init__(f"{decision.reason}: {decision.path}")


def _find_external_markers(path: Path) -> set[str]:
    markers: set[str] = set()
    current = path if path.is_dir() else path.parent
    for candidate in (current, *current.parents):
        name = candidate.name
        if name in _EXTERNAL_STORAGE_MARKERS:
            markers.add(name)
        for marker in (".git", ".obsidian"):
            if (candidate / marker).exists():
                markers.add(marker)
    return markers
