"""Profile layout quality checks (Dogfood / context-layering design)."""

from __future__ import annotations

import re

from sayane.core.models import SayaneProfile
from sayane.evaluators.sections import looks_like_structured_persona

TONE_MAX_LEN = 80
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w{2,}", re.IGNORECASE)
_MARKDOWN_HEADING_RE = re.compile(r"^#+\s")
_YAML_KEY_LINE_RE = re.compile(r"^[a-z][a-z0-9_]*:\s*.+", re.IGNORECASE)

_CAPTURE_PERSONA_GUIDANCE = (
    "Structured persona document detected. Do not approve into voice.tone or "
    "knowledge.concepts as a blob. Edit context/*.md per docs/context-layering-design.md "
    "and use short section-specific captures."
)


def capture_content_warnings(content: str) -> list[str]:
    """Warnings to return on Bridge /capture when content shape is risky."""
    if looks_like_structured_persona(content):
        return [_CAPTURE_PERSONA_GUIDANCE]
    return []


def validate_profile_quality(profile: SayaneProfile) -> list[str]:
    """Return human-readable warnings for profile layout issues."""
    warnings: list[str] = []
    warnings.extend(_validate_tone(profile.voice.tone))
    if profile.knowledge and profile.knowledge.concepts:
        warnings.extend(_validate_concepts(profile.knowledge.concepts))
    return warnings


def _validate_tone(tone: list[str]) -> list[str]:
    out: list[str] = []
    for i, item in enumerate(tone):
        label = f"voice.tone[{i}]"
        stripped = item.strip()
        if not stripped:
            out.append(f"{label}: empty entry")
            continue
        if len(stripped) > TONE_MAX_LEN:
            preview = stripped[:40] + "…" if len(stripped) > 40 else stripped
            out.append(
                f"{label}: exceeds {TONE_MAX_LEN} characters ({len(stripped)}): {preview!r}",
            )
        if _MARKDOWN_HEADING_RE.match(stripped):
            out.append(f"{label}: markdown heading belongs in context/, not voice.tone")
        if _YAML_KEY_LINE_RE.match(stripped):
            out.append(f"{label}: YAML key line belongs in context/ or identity, not voice.tone")
        if "ペルソナ" in stripped and len(stripped) < 40:
            out.append(f"{label}: persona title line should not be in voice.tone")
    return out


def _validate_concepts(concepts: list[str]) -> list[str]:
    out: list[str] = []
    for i, item in enumerate(concepts):
        label = f"knowledge.concepts[{i}]"
        stripped = item.strip()
        if _EMAIL_RE.search(stripped):
            out.append(f"{label}: email/PII should not be in knowledge.concepts")
        if len(stripped) > 120:
            out.append(f"{label}: long text belongs in context/*.md, not concepts list")
        if _MARKDOWN_HEADING_RE.match(stripped):
            out.append(f"{label}: markdown heading belongs in context/, not concepts")
    return out
