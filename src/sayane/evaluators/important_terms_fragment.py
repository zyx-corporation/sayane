"""Important-terms fragment extraction helpers."""

from __future__ import annotations

import re
from typing import Any

_IMPORTANT_TERMS_FRAGMENT_RE = re.compile(r"(?m)^\s*important_terms\s*:\s*$", re.IGNORECASE)
_LIST_ITEM_RE = re.compile(r"^\s*-\s*(.+?)\s*$")


def normalize_scalar(value: Any) -> str:
    """Normalize a YAML scalar-ish value for capture classification."""
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(normalize_scalar(v) for v in value if v is not None)
    return str(value).strip().strip('"\'')


def extract_important_terms_fragment(content: str) -> list[str]:
    """Extract list items from a partial `important_terms:` clipboard fragment."""
    lines = content.splitlines()
    terms: list[str] = []
    in_section = False
    section_indent = 0
    for line in lines:
        if not in_section:
            match = _IMPORTANT_TERMS_FRAGMENT_RE.match(line)
            if match:
                in_section = True
                section_indent = len(line) - len(line.lstrip())
            continue
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        if indent <= section_indent and not _LIST_ITEM_RE.match(line):
            break
        item = _LIST_ITEM_RE.match(line)
        if item:
            text = normalize_scalar(item.group(1))
            if text:
                terms.append(text)
    return terms
