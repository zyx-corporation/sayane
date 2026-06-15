"""YAML-like capture detection and syntax diagnostics."""

from __future__ import annotations

import re
from typing import Any

import yaml

from sayane.evaluators.important_terms_fragment import extract_important_terms_fragment

_BROKEN_INLINE_KEY_RE = re.compile(
    r'["\'][^"\']*["\'][ \t]{2,}[a-z][a-z0-9_]*:\s*',
    re.IGNORECASE,
)
_YAML_LIKE_RE = re.compile(
    r"^(persona|person|organization|development_preferences|writing_preferences|"
    r"communication_mode|major_projects|projects|values|identity|important_terms)\s*:",
    re.IGNORECASE | re.MULTILINE,
)
_MARKDOWN_HEADING_RE = re.compile(r"(?m)^#+\s+")
_MARKDOWN_BULLET_RE = re.compile(r"(?m)^\s*[-*•]\s+")

PERSONA_ROOT_KEYS = frozenset(
    {
        "persona",
        "person",
        "organization",
        "development_preferences",
        "writing_preferences",
        "communication_mode",
        "identity",
        "values",
        "projects",
        "major_projects",
    },
)


def looks_like_yaml_capture(content: str) -> bool:
    stripped = content.strip()
    if not stripped:
        return False
    if extract_important_terms_fragment(content):
        return True
    if _MARKDOWN_HEADING_RE.search(content) and _MARKDOWN_BULLET_RE.search(content):
        return False
    if stripped.startswith("{") or stripped.startswith("["):
        return True
    if _BROKEN_INLINE_KEY_RE.search(content):
        return True
    if re.search(r"(?m)^persona\s*:", content):
        return True
    return bool(_YAML_LIKE_RE.search(stripped))


def detect_yaml_syntax_error(content: str) -> str | None:
    if _BROKEN_INLINE_KEY_RE.search(content):
        m = _BROKEN_INLINE_KEY_RE.search(content)
        if m:
            tail = content[m.start() : m.start() + 80]
            key_match = re.search(r"([a-z][a-z0-9_]*):\s*$", tail, re.IGNORECASE)
            if key_match:
                return f"YAML parse failed near {key_match.group(1)}"
        return "YAML parse failed: inline key after quoted value"
    try:
        yaml.safe_load(content)
        return None
    except yaml.YAMLError as err:
        msg = str(err).split("\n")[0]
        return f"YAML parse failed: {msg[:120]}"


def try_parse_yaml(content: str) -> tuple[Any | None, str | None]:
    err = detect_yaml_syntax_error(content)
    if err:
        return None, err
    try:
        parsed = yaml.safe_load(content)
    except yaml.YAMLError as err:
        return None, f"YAML parse failed: {str(err).splitlines()[0][:120]}"
    if parsed is None:
        return None, "YAML parse failed: empty document"
    return parsed, None


def top_level_yaml_keys(parsed: dict[str, Any]) -> set[str]:
    return {str(k).lower() for k in parsed.keys()}


def persona_document_keys(parsed: dict[str, Any]) -> set[str]:
    keys = top_level_yaml_keys(parsed)
    return keys & PERSONA_ROOT_KEYS
