"""Export noise filtering helpers."""

from __future__ import annotations

from typing import Any

EXPORT_NOISE_SUBSTRINGS: tuple[str, ...] = (
    "Capture",
    "Candidate",
    "Popup",
    "Sayane —",
    "Side Panel",
    "Debug",
    "このフィルタ",
    "差分ビュー",
    "候補メタデータ",
    "元の文脈",
    "候補文脈",
    "RDE評価",
    "注意点",
    "保存済み Sayane 文脈",
    "提案される変更",
)
EXPORT_NOISE_EXACT: frozenset[str] = frozenset({"debug_only", "transient_session", "ui_noise"})


def is_noise_value(value: str) -> bool:
    stripped = value.strip()
    if not stripped:
        return True
    if stripped.lower() in EXPORT_NOISE_EXACT:
        return True
    return any(pattern.lower() in stripped.lower() for pattern in EXPORT_NOISE_SUBSTRINGS)


def filter_noise_from_list(items: list[Any]) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for item in items:
        if isinstance(item, str):
            if is_noise_value(item):
                continue
            key = item.strip().lower()
            if key in seen:
                continue
            seen.add(key)
        result.append(item)
    return result


def clean_export_data(data: dict[str, Any]) -> dict[str, Any]:
    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if isinstance(value, list):
            filtered = filter_noise_from_list(value)
            if filtered:
                cleaned[key] = filtered
        elif isinstance(value, dict):
            nested = clean_export_data(value)
            if nested:
                cleaned[key] = nested
        elif isinstance(value, str):
            if not is_noise_value(value):
                cleaned[key] = value
        elif value is not None:
            cleaned[key] = value
    return cleaned
