"""Build metadata for Bridge startup and health."""

from __future__ import annotations

import re

import pytest

from sayane import __version__
from sayane.core import build_info
from sayane.core.build_info import (
    format_build_info_startup_line,
    format_source_updated_at,
    get_build_info,
)


def test_get_build_info_has_version_and_timestamp() -> None:
    info = get_build_info()
    assert info.version == __version__
    assert re.match(r"^\d{4}-\d{2}-\d{2}T", info.source_updated_at)
    payload = info.as_dict()
    assert payload["component"] == "sayane"
    assert payload["version"] == __version__


def test_format_source_updated_at_readable() -> None:
    formatted = format_source_updated_at("2026-06-02T10:15:30+09:00")
    assert "2026-06-02" in formatted
    assert "10:15:30" in formatted


def test_get_build_info_prefers_newer_mtime_over_git(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        build_info,
        "_git_latest_commit_time",
        lambda _path: "2020-01-01T00:00:00+00:00",
    )
    monkeypatch.setattr(
        build_info,
        "_max_mtime_iso",
        lambda _path: "2026-06-04T12:00:00+00:00",
    )
    build_info.get_build_info.cache_clear()
    info = get_build_info()
    assert info.source_updated_at.startswith("2026-06-04")


def test_format_build_info_startup_line_is_english() -> None:
    from sayane.core.build_info import BuildInfo

    line = format_build_info_startup_line(
        BuildInfo(version="1.0.4", source_updated_at="2026-06-04T12:00:00+00:00"),
    )
    assert "codebase updated" in line
    assert "コードベース" not in line
    assert line.startswith("Sayane 1.0.4")
