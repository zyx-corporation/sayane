"""Resolve bundled JSON Schema paths (OSS + installed wheel)."""

from pathlib import Path


def schemas_dir() -> Path:
    bundled = Path(__file__).resolve().parent / "bundled_schemas"
    if bundled.is_dir():
        return bundled
    return Path(__file__).resolve().parents[2] / "schemas"
