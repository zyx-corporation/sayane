"""Build Prompt IR from Sayane Profile."""

from pathlib import Path

from sayane.core.canonical_terms import attach_canonical_terms_to_ir, merge_canonical_terms
from sayane.core.models import PromptIR, SayaneProfile, SayaneProjectProfile
from sayane.core.project_loader import load_project_profile
from sayane.storage.markdown import normalize_markdown

PROMPT_IR_VERSION = "0.1.0"
_MAX_CONTEXT_CHARS = 32_000


def build_prompt_ir(
    profile: SayaneProfile,
    instruction: str | None = None,
    *,
    profile_root: Path | None = None,
    project_profile: SayaneProjectProfile | None = None,
    load_context_bodies: bool = True,
) -> PromptIR:
    """Compile profile fields into a structured Prompt IR."""
    resolved_project = project_profile
    if resolved_project is None and profile_root is not None:
        resolved_project = load_project_profile(profile_root)

    system = _build_system_lines(profile)
    context = _build_context_lines(profile, profile_root, load_context_bodies)
    constraints = _build_constraint_lines(profile)
    instructions = [instruction] if instruction else []

    ir = PromptIR(
        version=PROMPT_IR_VERSION,
        system=system,
        context=context,
        instruction=instructions,
        constraints=constraints,
        examples=[],
    )
    merged_terms = merge_canonical_terms(profile, resolved_project)
    attach_canonical_terms_to_ir(ir, merged_terms)
    return ir


def _build_system_lines(profile: SayaneProfile) -> list[str]:
    identity = profile.identity
    lines = [f"You are assisting {identity.name}."]
    if identity.preferred_name:
        lines.append(f"Preferred name: {identity.preferred_name}.")
    if identity.roles:
        lines.append(f"Roles: {', '.join(identity.roles)}.")
    if profile.voice.default_language:
        lines.append(f"Default language: {profile.voice.default_language}.")
    if profile.voice.tone:
        lines.append(f"Tone: {', '.join(profile.voice.tone)}.")
    if profile.values.core:
        lines.append(f"Core values: {', '.join(profile.values.core)}.")
    if profile.knowledge and profile.knowledge.concepts:
        lines.append(f"Key concepts: {', '.join(profile.knowledge.concepts)}.")
    return lines


def _build_context_lines(
    profile: SayaneProfile,
    profile_root: Path | None,
    load_context_bodies: bool,
) -> list[str]:
    lines: list[str] = []
    idx = profile.context_index
    if idx.entrypoint:
        lines.append(f"Context entrypoint: {idx.entrypoint}")
    if idx.handoff:
        lines.append(f"Context handoff: {idx.handoff}")
    if idx.entries:
        lines.append(f"Context index entries: {', '.join(idx.entries)}")

    if profile_root is not None and load_context_bodies:
        for rel in _context_paths_to_load(idx):
            body = _read_context_body(profile_root, rel)
            if body:
                lines.append(f"--- {rel} ---\n{body}")
    return lines


def _context_paths_to_load(idx: object) -> list[str]:
    paths: list[str] = []
    seen: set[str] = set()
    for rel in (
        getattr(idx, "entrypoint", None),
        getattr(idx, "handoff", None),
        *getattr(idx, "entries", []),
    ):
        if rel and rel not in seen:
            seen.add(rel)
            paths.append(rel)
    return paths


def _read_context_body(profile_root: Path, rel_path: str) -> str | None:
    candidate = (profile_root / rel_path).resolve()
    root = profile_root.resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    if not candidate.is_file():
        return None
    text = normalize_markdown(candidate.read_text(encoding="utf-8"))
    if len(text) > _MAX_CONTEXT_CHARS:
        text = text[:_MAX_CONTEXT_CHARS] + "\n…(truncated)"
    return text


def _build_constraint_lines(profile: SayaneProfile) -> list[str]:
    response = profile.policy.response
    if response is None:
        return []
    lines: list[str] = []
    if response.avoid:
        lines.append(f"Avoid: {', '.join(response.avoid)}.")
    if response.prefer:
        lines.append(f"Prefer: {', '.join(response.prefer)}.")
    return lines
