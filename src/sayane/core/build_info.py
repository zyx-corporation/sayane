"""Version and codebase freshness metadata for CLI, Bridge, and tooling."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from pathlib import Path

import sayane

_PKG_ROOT = Path(__file__).resolve().parent


@dataclass(frozen=True)
class BuildInfo:
    version: str
    source_updated_at: str
    component: str = "sayane"

    def as_dict(self) -> dict[str, str]:
        return {
            "version": self.version,
            "source_updated_at": self.source_updated_at,
            "component": self.component,
        }


def _repo_root() -> Path:
    return _PKG_ROOT.parent.parent.parent


def _git_latest_commit_time(path: Path) -> str | None:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(_repo_root()),
                "log",
                "-1",
                "--format=%cI",
                "--",
                str(path.relative_to(_repo_root())),
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=3,
        )
        text = result.stdout.strip()
        return text or None
    except (OSError, subprocess.SubprocessError):
        return None


def _max_mtime_iso(directory: Path) -> str:
    latest: float | None = None
    if directory.is_dir():
        for file in directory.rglob("*"):
            if file.is_file():
                mtime = file.stat().st_mtime
                if latest is None or mtime > latest:
                    latest = mtime
    if latest is None:
        return datetime.now(UTC).isoformat(timespec="seconds")
    return datetime.fromtimestamp(latest, tz=UTC).isoformat(timespec="seconds")


def _parse_iso_timestamp(iso_timestamp: str) -> datetime | None:
    text = iso_timestamp.strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except ValueError:
        return None


def _latest_source_update_iso(directory: Path) -> str:
    """Latest of git commit time and on-disk mtime (includes uncommitted edits)."""
    candidates: list[str] = []
    git_time = _git_latest_commit_time(directory)
    if git_time:
        candidates.append(git_time)
    candidates.append(_max_mtime_iso(directory))
    best = candidates[0]
    best_dt = _parse_iso_timestamp(best)
    for candidate in candidates[1:]:
        candidate_dt = _parse_iso_timestamp(candidate)
        if candidate_dt is None:
            continue
        if best_dt is None or candidate_dt > best_dt:
            best = candidate
            best_dt = candidate_dt
    return best


@lru_cache(maxsize=1)
def get_build_info() -> BuildInfo:
    """Return Sayane core version and latest change time under src/sayane."""
    src_root = _PKG_ROOT.parent
    updated = _latest_source_update_iso(src_root)
    return BuildInfo(version=sayane.__version__, source_updated_at=updated)


def format_source_updated_at(iso_timestamp: str) -> str:
    """Human-readable timestamp preserving the source timestamp's own offset."""
    dt = _parse_iso_timestamp(iso_timestamp)
    if dt is None:
        text = iso_timestamp.strip()
        return text[:19].replace("T", " ") if text else "—"
    return dt.strftime("%Y-%m-%d %H:%M:%S %z")


def format_build_info_startup_line(build: BuildInfo) -> str:
    """English startup line for CLI / Bridge (locale-independent)."""
    updated = format_source_updated_at(build.source_updated_at)
    return f"Sayane {build.version} · codebase updated {updated}"
