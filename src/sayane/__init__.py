"""Sayane core package."""

from __future__ import annotations

from importlib import metadata


def _read_version() -> str:
    try:
        return metadata.version("sayane")
    except metadata.PackageNotFoundError:
        return "0+unknown"


__version__ = _read_version()

__all__ = ["__version__"]
