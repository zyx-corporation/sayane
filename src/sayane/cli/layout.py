"""Initialize non-destructive Sayane managed directory layout."""

from __future__ import annotations

from pathlib import Path

from sayane.cli.paths import (
    e2e_prompts_dir,
    e2e_user_data_dir,
    model_prompts_dir,
    provider_prompts_dir,
    sayane_home,
    target_prompts_dir,
)

README_TEXT = """# Sayane Managed Directory

This directory is managed by Sayane.

Layout:

- `profiles/`: persona profiles and context files.
- `prompts/targets/`: target-level prompt adaptations, e.g. ChatGPT, Claude, Gemini.
- `prompts/models/`: model-specific prompt optimizations, e.g. Qwen, DeepSeek-R1-Distill.
- `prompts/providers/`: provider/UI-specific constraints, e.g. Open WebUI, LibreChat.
- `e2e/user-data/`: browser profile state for real DOM E2E only.
- `e2e/prompts/`: test-only E2E prompts and markers.

Do not treat `e2e/user-data/` as a canonical prompt source. It is opaque browser state.
"""

TARGETS_README = """# Target Prompt Adaptations

Store target-level prompt adaptations here.

Examples:

- `chatgpt.yaml`
- `claude.yaml`
- `gemini.yaml`
- `deepseek.yaml`
- `openai_compatible.yaml`
- `plain_text.yaml`

These files should remain auditable and diffable.
"""

MODELS_README = """# Model Prompt Optimizations

Store model-specific prompt optimizations here.

Examples:

- `qwen2.5-7b-instruct.yaml`
- `deepseek-r1-distill-qwen-7b.yaml`
- `elyza-japanese-llama-2-7b-instruct.yaml`

Model-specific prompt tuning belongs here, not in browser user-data directories.
"""

PROVIDERS_README = """# Provider Prompt Constraints

Store provider/UI-specific prompt constraints here.

Examples:

- `local-openwebui.yaml`
- `local-librechat.yaml`
- `local-custom.yaml`

Provider constraints describe UI or delivery quirks. They are distinct from model capability.
"""

E2E_USER_DATA_README = """# E2E Browser User Data

This directory contains Chromium persistent profiles used by real DOM E2E.

Expected layout:

- `chatgpt/`
- `claude/`
- `gemini/`
- `deepseek/`
- `local-openwebui/`

Do not store canonical prompts here. This area may contain cookies, localStorage,
IndexedDB, and other opaque browser state.
"""

E2E_PROMPTS_README = """# E2E Prompts

Store test-only E2E prompt fixtures here.

These prompts may contain markers such as `SAYANE_E2E_MARKER::*` and are not the
canonical source for production prompt optimization.
"""


def _write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def ensure_sayane_layout() -> None:
    """Create the non-destructive Sayane directory skeleton.

    Existing files are never overwritten. This can be safely called from `sayane init`
    even when the main profile already exists.
    """
    root = sayane_home()
    targets = target_prompts_dir()
    models = model_prompts_dir()
    providers = provider_prompts_dir()
    e2e_users = e2e_user_data_dir()
    e2e_prompts = e2e_prompts_dir()

    for directory in (root, targets, models, providers, e2e_users, e2e_prompts):
        directory.mkdir(parents=True, exist_ok=True)

    _write_if_missing(root / "README.md", README_TEXT)
    _write_if_missing(targets / "README.md", TARGETS_README)
    _write_if_missing(models / "README.md", MODELS_README)
    _write_if_missing(providers / "README.md", PROVIDERS_README)
    _write_if_missing(e2e_users / "README.md", E2E_USER_DATA_README)
    _write_if_missing(e2e_prompts / "README.md", E2E_PROMPTS_README)
