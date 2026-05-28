"""Bounded text matching for Level-1 heuristics.

All marker checks use token, phrase, dot-path, or YAML-key boundaries so that
substring accidents (e.g. ``Melotone:`` matching ``tone:``, ``secretary`` matching
``secret``) do not occur.
"""

from __future__ import annotations

import re

# Token boundary: hyphen does not glue tokens (``top-secret`` ≠ ``secret``).
_L = r"(?<![a-z0-9_\-])"
_R = r"(?![a-z0-9_\-])"

# Dot-path boundary (also excludes adjacent dots).
_PATH_L = r"(?<![a-z0-9_.])"
_PATH_R = r"(?![a-z0-9_.])"


def contains_word(content: str, word: str) -> bool:
    """Whole-word match (case-insensitive)."""
    if not word:
        return False
    pattern = re.compile(rf"{_L}{re.escape(word)}{_R}", re.IGNORECASE)
    return bool(pattern.search(content))


def contains_phrase(content: str, phrase: str) -> bool:
    """Multi-token phrase; tokens are word-bounded, separated by whitespace."""
    tokens = phrase.split()
    if not tokens:
        return False
    inner = r"\s+".join(re.escape(t) for t in tokens)
    pattern = re.compile(rf"{_L}{inner}{_R}", re.IGNORECASE)
    return bool(pattern.search(content))


def contains_dot_path(content: str, path: str) -> bool:
    """Sayane-style dotted path (e.g. ``values.core``), not a substring."""
    if not path:
        return False
    escaped = re.escape(path).replace(r"\.", r"\.")
    pattern = re.compile(rf"{_PATH_L}{escaped}{_PATH_R}", re.IGNORECASE)
    return bool(pattern.search(content))


def has_yaml_key(content: str, key: str) -> bool:
    """YAML key at a token boundary followed by ``:`` (e.g. ``tone:``, not ``Melotone:``)."""
    if not key:
        return False
    pattern = re.compile(rf"{_L}{re.escape(key)}\s*:", re.IGNORECASE)
    return bool(pattern.search(content))


def has_core_values_phrase(content: str) -> bool:
    """English phrase ``core value`` / ``core values`` as distinct tokens."""
    return bool(
        re.search(rf"{_L}core\s+values?{_R}", content, re.IGNORECASE),
    )


def has_imperative_always(content: str) -> bool:
    """``always`` followed by whitespace (avoids ``always-on``; matches ``always use``)."""
    return bool(re.search(rf"{_L}always\s+", content, re.IGNORECASE))


def has_imperative_never(content: str) -> bool:
    """``never`` followed by whitespace (avoids ``nevertheless``)."""
    return bool(re.search(rf"{_L}never\s+", content, re.IGNORECASE))


def contains_any_word(content: str, words: tuple[str, ...]) -> bool:
    return any(contains_word(content, w) for w in words)


def contains_any_phrase(content: str, phrases: tuple[str, ...]) -> bool:
    return any(contains_phrase(content, p) for p in phrases)


def contains_any_dot_path(content: str, paths: tuple[str, ...]) -> bool:
    return any(contains_dot_path(content, p) for p in paths)
