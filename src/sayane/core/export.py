"""Context Portability export public facade."""

from __future__ import annotations

from sayane.core.export_markdown_compact import export_markdown_compact
from sayane.core.export_markdown_generic import export_markdown_generic
from sayane.core.export_noise import (
    clean_export_data,
    filter_noise_from_list,
    is_noise_value,
)
from sayane.core.export_prompt import export_prompt
from sayane.core.export_scope import SCOPE_SECTIONS, pick_profile_sections
from sayane.core.export_yaml import export_yaml
from sayane.core.models import SayaneProfile

# Backward-compatible aliases for older internal tests/imports.
_is_noise_value = is_noise_value
_filter_noise_from_list = filter_noise_from_list
_clean_export_data = clean_export_data
_pick_profile_sections = pick_profile_sections
_export_markdown_generic = export_markdown_generic
_export_markdown_compact = export_markdown_compact


def export_markdown(profile: SayaneProfile, scopes: list[str], target: str = "generic") -> str:
    if target == "chatgpt":
        return export_markdown_compact(profile, scopes, "ChatGPT")
    if target in ("claude", "anthropic"):
        return export_markdown_compact(profile, scopes, "Claude")
    if target in ("gemini", "google"):
        return export_markdown_compact(profile, scopes, "Gemini")
    if target == "deepseek":
        return export_markdown_compact(profile, scopes, "DeepSeek")
    return export_markdown_generic(profile, scopes, target)


__all__ = [
    "SCOPE_SECTIONS",
    "export_yaml",
    "export_markdown",
    "export_prompt",
]
