"""Markdown normalization for vault import and context storage."""

import re

_BOM = "\ufeff"
_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)


def normalize_markdown(text: str) -> str:
    """Normalize line endings, strip BOM, trim trailing whitespace per line."""
    if text.startswith(_BOM):
        text = text[len(_BOM) :]
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _TRAILING_WS.sub("", text)
    text = text.strip("\n")
    if text:
        return text + "\n"
    return ""
