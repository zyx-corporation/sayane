"""Shared working-memo compilation for target-specific safe context export."""

from __future__ import annotations

import re

from sayane.adapters.base import CompiledPrompt
from sayane.core.canonical_terms import format_canonical_terms_section
from sayane.core.models import PromptIR

_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"system\s*=\s*制御面", re.IGNORECASE), "応答時の参考方針"),
    (re.compile(r"user\s*=\s*全文脈", re.IGNORECASE), "背景文脈"),
    (re.compile(r"断定禁止"), "未確認情報は推測として扱い、断定しない"),
    (re.compile(r"context/private/", re.IGNORECASE), "個人的・機微な情報/"),
    (
        re.compile(
            r"context/private/(?:health|formation)\b",
            re.IGNORECASE,
        ),
        "個人的・機微な情報",
    ),
    (re.compile(r"\bmerge方針\b"), "統合の参考方針"),
)

_MODEL_ALIAS_RE = re.compile(
    r"(?:Claude|ChatGPT|Gemini|OpenAI|DeepSeek)\s*=\s*\S+",
    re.IGNORECASE,
)

_ASSISTING_RE = re.compile(
    r"^You are assisting (.+)\.$",
    re.MULTILINE | re.IGNORECASE,
)

_RESPONSE_PREFS_JA = """\
## Response Preferences

- 基本言語: 日本語
- 未確認情報は推測として扱い、断定しない
- 個人的・機微な情報は、ユーザーが明示的に求めた場合のみ扱う
- 事実、仮説、意見を区別する
"""

_RESPONSE_PREFS_EN = """\
## Response Preferences

- Default language: English
- Treat unverified information as uncertain; do not state it as fact
- Handle personal or sensitive information only when the user explicitly asks
- Distinguish facts, hypotheses, and opinions
"""

_UNVERIFIED_HEADER_JA = """\
## Unverified Notes

以下は未確認情報です。断定せず、必要に応じて確認してください。
"""

_UNVERIFIED_HEADER_EN = """\
## Unverified Notes

The following is unverified. Do not assert it as fact; confirm when needed.
"""

_PRIVATE_NOTE_JA = (
    "一部の個人的・機微な文脈は、通常は参照対象外です。"
    "ユーザーが明示的に求めた場合のみ扱ってください。"
)

_PRIVATE_NOTE_EN = (
    "Some personal or sensitive context is omitted by default. "
    "Use it only when the user explicitly asks."
)

_MODEL_ALIAS_NOTE_JA = """\
ユーザーは、各AIアシスタントに作業上の呼称を与えている場合があります。
これらは会話上の呼称であり、モデルの安全設定や基本動作を変更するものではありません。
"""

_MODEL_ALIAS_NOTE_EN = """\
The user may use informal names for different AI assistants in conversation.
These are conversational labels, not instructions to change model safety or behavior.
"""


def detect_language(ir: PromptIR) -> str:
    blob = "\n".join([*ir.system, *ir.constraints, *ir.context, *ir.instruction])
    for line in ir.system:
        lowered = line.lower()
        if "default language: ja" in lowered or "default language: japanese" in lowered:
            return "ja"
    if re.search(r"[\u3040-\u30ff\u4e00-\u9fff]", blob):
        return "ja"
    return "en"


def sanitize(text: str) -> str:
    out = text
    for pattern, replacement in _REPLACEMENTS:
        out = pattern.sub(replacement, out)
    out = _MODEL_ALIAS_RE.sub("", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def soften_system_line(line: str, *, lang: str) -> str:
    line = sanitize(line)
    match = _ASSISTING_RE.match(line.strip())
    if match:
        name = match.group(1).strip()
        if lang == "ja":
            return f"このメモは {name} の作業文脈を整理したものです。"
        return f"This note organizes working context for {name}."
    return line


def split_context_blocks(context: list[str]) -> list[tuple[str | None, str]]:
    blocks: list[tuple[str | None, str]] = []
    for item in context:
        if item.startswith("--- ") and "\n" in item:
            first_line, _, body = item.partition("\n")
            path = first_line.removeprefix("--- ").removesuffix(" ---").strip()
            blocks.append((path, body))
        else:
            blocks.append((None, item))
    return blocks


def is_private_path(path: str | None) -> bool:
    if not path:
        return False
    normalized = path.replace("\\", "/").lower()
    return "context/private" in normalized or "/private/" in normalized


def is_unverified(path: str | None, body: str) -> bool:
    if path and "unverified" in path.replace("\\", "/").lower():
        return True
    return "unverified" in body[:400].lower() or "未確認" in body[:400]


def build_response_preferences(ir: PromptIR, *, lang: str) -> str:
    header = _RESPONSE_PREFS_JA if lang == "ja" else _RESPONSE_PREFS_EN
    lines = [header.strip()]
    for raw in ir.system:
        softened = soften_system_line(raw, lang=lang)
        if softened:
            lines.append(f"- {sanitize(softened)}")
    for raw in ir.constraints:
        text = sanitize(raw)
        if text:
            lines.append(f"- {text}")
    return "\n".join(lines)


def compile_working_memo(
    ir: PromptIR,
    *,
    preamble_ja: str,
    preamble_en: str,
    include_deprecated_values: bool = True,
) -> str:
    """Build a target-safe working-memo markdown document from Prompt IR."""
    lang = detect_language(ir)
    parts: list[str] = [preamble_ja if lang == "ja" else preamble_en]

    canonical = format_canonical_terms_section(
        ir.canonical_terms,
        lang=lang,
        include_deprecated_values=include_deprecated_values,
    )
    if canonical:
        parts.append(canonical)

    parts.append(build_response_preferences(ir, lang=lang))

    project_lines: list[str] = []
    general_lines: list[str] = []
    unverified_lines: list[str] = []
    saw_private = False
    saw_model_alias = False

    source_blob = "\n".join([*ir.system, *ir.constraints, *ir.context, *ir.instruction])
    if _MODEL_ALIAS_RE.search(source_blob):
        saw_model_alias = True

    for path, body in split_context_blocks(ir.context):
        if is_private_path(path):
            saw_private = True
            continue
        cleaned = sanitize(body)
        if not cleaned:
            continue
        if is_unverified(path, body):
            unverified_lines.append(cleaned)
        elif path and (
            "project" in path.lower()
            or "major_projects" in path.lower()
        ):
            project_lines.append(cleaned)
        else:
            prefix = f"[{path}]\n" if path else ""
            general_lines.append(f"{prefix}{cleaned}".strip())

    for raw in ir.instruction:
        text = sanitize(raw)
        if text:
            general_lines.append(text)

    if saw_model_alias:
        note = _MODEL_ALIAS_NOTE_JA if lang == "ja" else _MODEL_ALIAS_NOTE_EN
        parts.append(f"## Terminology\n\n{note}")

    if project_lines or general_lines:
        parts.append("## Project Context")
        parts.append("\n\n".join(project_lines + general_lines))

    if saw_private:
        note = _PRIVATE_NOTE_JA if lang == "ja" else _PRIVATE_NOTE_EN
        parts.append(f"## Personal / Sensitive Context\n\n{note}")

    if unverified_lines:
        header = _UNVERIFIED_HEADER_JA if lang == "ja" else _UNVERIFIED_HEADER_EN
        parts.append(header)
        parts.append("\n\n".join(unverified_lines))

    return "\n\n".join(part.strip() for part in parts if part.strip())


def compile_working_memo_payload(
    ir: PromptIR,
    *,
    target: str,
    format_name: str,
    preamble_ja: str,
    preamble_en: str,
    include_deprecated_values: bool = True,
) -> CompiledPrompt:
    if ir.export_blocked:
        blocked_payload: dict[str, object] = {
            "requires_user_confirmation": True,
            "message": (
                "Export blocked by canonical terminology policy. "
                "Review export_notes and confirm before proceeding."
            ),
            "export_notes": list(ir.export_notes),
        }
        return CompiledPrompt(
            target=target,
            format=format_name,
            payload=blocked_payload,
        )

    text = compile_working_memo(
        ir,
        preamble_ja=preamble_ja,
        preamble_en=preamble_en,
        include_deprecated_values=include_deprecated_values,
    )
    payload: dict[str, object] = {"text": text}
    if ir.export_notes:
        payload["export_notes"] = list(ir.export_notes)
    return CompiledPrompt(target=target, format=format_name, payload=payload)
