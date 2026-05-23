"""Git commit integration for profile stores."""

import subprocess
from pathlib import Path


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
        ("user.name", "Omomuki"),
        ("user.email", "omomuki@local"),
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

    profile_file = profile_dir / "omomuki.profile.yaml"
    if profile_file.exists():
        _run_git(profile_dir, "add", "omomuki.profile.yaml")
    context_dir = profile_dir / "context"
    if context_dir.exists():
        _run_git(profile_dir, "add", "context")

    status = _run_git(profile_dir, "status", "--porcelain")
    if not status:
        return ""

    _ensure_local_git_identity(profile_dir)
    _run_git(profile_dir, "commit", "-m", message)
    return _run_git(profile_dir, "rev-parse", "HEAD")
