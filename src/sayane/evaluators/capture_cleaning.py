"""Remove LLM UI chrome from page captures."""

from __future__ import annotations

import re

# Shared navigation / chrome strings (ja + en).
_UI_NOISE_EXACT: frozenset[str] = frozenset(
    {
        "チャット履歴",
        "新しいチャット",
        "チャットを検索",
        "ライブラリ",
        "アプリ",
        "プロジェクト",
        "最近",
        "共有する",
        "思考時間",
        "情報源",
        "ChatGPT の回答は必ずしも正しいとは限りません",
        "ChatGPT can make mistakes. Check important info.",
        "1Passwordメニューが利用できます",
        "1Password",
        "Chat history",
        "New chat",
        "Search chats",
        "Library",
        "Apps",
        "Projects",
        "Recent",
        "Share",
        "Sources",
        "Copy",
        "Regenerate",
        "Good response",
        "Bad response",
    },
)

_UI_NOISE_PREFIXES: tuple[str, ...] = (
    "1Password",
    "ChatGPT",
    "Claude",
    "Gemini",
    "DeepSeek",
)

_TITLE_URL_RE = re.compile(r"^Title:\s*.+\nURL:\s*.+\n*", re.IGNORECASE | re.MULTILINE)


def is_ui_noise_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if stripped in _UI_NOISE_EXACT:
        return True
    if any(stripped.startswith(prefix) for prefix in _UI_NOISE_PREFIXES):
        if len(stripped) < 80:
            return True
    if stripped.startswith("©") or stripped.endswith("…"):
        return True
    return False


def clean_capture_text(text: str) -> tuple[str, bool]:
    """Return (cleaned_text, ui_noise_detected)."""
    body = _TITLE_URL_RE.sub("", text, count=1).strip()
    lines = body.splitlines()
    kept: list[str] = []
    noise_hits = 0
    for line in lines:
        if is_ui_noise_line(line):
            noise_hits += 1
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    ui_detected = noise_hits > 0 or (
        len(lines) > 0 and noise_hits / max(len(lines), 1) > 0.15
    )
    return cleaned, ui_detected


def display_summary_from_text(text: str, *, max_len: int = 280) -> str:
    compact = " ".join(ln.strip() for ln in text.splitlines() if ln.strip())
    if len(compact) <= max_len:
        return compact
    return f"{compact[: max_len - 1]}…"
