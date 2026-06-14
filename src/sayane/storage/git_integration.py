"""Git commit integration for profile stores.

Git integration is retained as an explicit legacy/manual integration point.
Community FileSystem storage keeps legacy auto-commit compatibility until the
Local Vault production backend is finalized.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path


LEGACY_GIT_AUTOCOMMIT_ENV = "SAYANE_ENABLE_LEGACY_GIT_AUTOCOMMIT"


class GitError(RuntimeError):
    """Git command failed."""


def _run_git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise GitError(result.stderr.strip() or result.stdout.strip() or "git failed")
    return result.stdout.strip()


def is_git_repo(path: Path) -> bool:
    try:
        _run_git(path, "rev-parse", "--git-dir")
        return True
    except GitError:
        return False


def init_repo(path: Path) -> None:
    _run_git(path, "init")
    _ensure_local_git_identity(path)


def _ensure_local_git_identity(profile_dir: Path) -> None:
    """Set repo-local author if missing (CI-friendly; does not touch global config)."""
    for key, value in (
        ("user.name", "Sayane"),
        ("user.email", "sayane@local"),
    ):
        try:
            _run_git(profile_dir, "config", key)
        except GitError:
            _run_git(profile_dir, "config", key, value)


def commit_profile_store(
    profile_dir: Path,
    message: str,
    *,
    init: bool = False,
) -> str:
    """Stage profile yaml, context/, and commit. Returns commit hash or empty if nothing."""
    profile_dir = profile_dir.resolve()
    if not is_git_repo(profile_dir):
        if not init:
            raise GitError(f"Not a git repository: {profile_dir}. Pass --init to create one.")
        init_repo(profile_dir)

    profile_file = profile_dir / "sayane.profile.yaml"
    if profile_file.exists():
        _run_git(profile_dir, "add", "sayane.profile.yaml")
    context_dir = profile_dir / "context"
    if context_dir.exists():
        _run_git(profile_dir, "add", "context")

    status = _run_git(profile_dir, "status", "--porcelain")
    if not status:
        return ""

    _ensure_local_git_identity(profile_dir)
    _run_git(profile_dir, "commit", "-m", message)
    return _run_git(profile_dir, "rev-parse", "HEAD")


def legacy_git_autocommit_enabled() -> bool:
    """Return whether legacy Git auto-commit has been explicitly disabled.

    Historically, the Community FileSystem backend auto-committed local profile
    changes. Tests and CLI docs still rely on that behavior. The environment
    flag remains accepted; setting it to ``0`` or ``false`` disables the legacy
    path for local experiments.
    """
    value = os.environ.get(LEGACY_GIT_AUTOCOMMIT_ENV)
    if value is None:
        return True
    return value.lower() not in {"0", "false", "no", "off"}


def auto_commit_profile_store(profile_dir: Path, message: str) -> str:
    """Auto-init Git and commit profile changes when legacy compatibility is enabled."""
    if not legacy_git_autocommit_enabled():
        return ""
    try:
        return commit_profile_store(profile_dir, message, init=True)
    except GitError:
        return ""
