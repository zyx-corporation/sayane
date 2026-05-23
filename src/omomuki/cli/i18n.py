"""CLI message localization."""

from __future__ import annotations

import json
import os
import sys
from functools import lru_cache
from importlib import resources
from typing import Any

_SUPPORTED = frozenset({"en", "ja"})
_DEFAULT = "en"
_locale = _DEFAULT


def resolve_locale(explicit: str | None = None) -> str:
    """Resolve locale from explicit value or environment."""
    if explicit:
        return _normalize(explicit)
    omomuki_lang = os.environ.get("OMOMUKI_LANG")
    if omomuki_lang:
        return _normalize(omomuki_lang)
    lang = os.environ.get("LANG")
    if lang:
        return _normalize(lang)
    return _DEFAULT


def _normalize(code: str) -> str:
    base = code.strip().replace("_", "-").split("-")[0].lower()
    return base if base in _SUPPORTED else _DEFAULT


def set_locale(code: str | None) -> str:
    """Set active locale; returns normalized code."""
    global _locale
    _locale = resolve_locale(code)
    _messages.cache_clear()
    return _locale


def get_locale() -> str:
    return _locale


def parse_lang_from_argv(argv: list[str]) -> str | None:
    """Extract --lang value from argv before Typer runs."""
    for i, arg in enumerate(argv):
        if arg == "--lang" and i + 1 < len(argv):
            return argv[i + 1]
        if arg.startswith("--lang="):
            return arg.split("=", 1)[1]
    return None


def init_locale_from_argv(argv: list[str] | None = None) -> str:
    """Initialize locale from argv and environment."""
    args = argv if argv is not None else sys.argv[1:]
    explicit = parse_lang_from_argv(args)
    return set_locale(explicit)


def t(key: str, **kwargs: Any) -> str:
    """Translate message key; falls back to English then key name."""
    catalog = _messages()
    template = catalog.get(key) or _fallback_en().get(key) or key
    if kwargs:
        return template.format(**kwargs)
    return template


@lru_cache(maxsize=4)
def _messages() -> dict[str, str]:
    return _load_catalog(get_locale())


@lru_cache(maxsize=1)
def _fallback_en() -> dict[str, str]:
    return _load_catalog("en")


def _load_catalog(locale: str) -> dict[str, str]:
    try:
        data = (
            resources.files("omomuki.cli")
            .joinpath("locale", f"{locale}.json")
            .read_text(encoding="utf-8")
        )
    except (FileNotFoundError, ModuleNotFoundError, TypeError):
        if locale == _DEFAULT:
            return {}
        return _load_catalog(_DEFAULT)
    parsed = json.loads(data)
    if not isinstance(parsed, dict):
        return {}
    return {str(k): str(v) for k, v in parsed.items()}
