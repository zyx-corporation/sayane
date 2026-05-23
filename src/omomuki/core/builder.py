"""Build Prompt IR from Omomuki Profile."""

from omomuki.core.models import OmomukiProfile, PromptIR

PROMPT_IR_VERSION = "0.1.0"


def build_prompt_ir(profile: OmomukiProfile, instruction: str | None = None) -> PromptIR:
    """Compile profile fields into a structured Prompt IR."""
    system = _build_system_lines(profile)
    context = _build_context_lines(profile)
    constraints = _build_constraint_lines(profile)
    instructions = [instruction] if instruction else []

    return PromptIR(
        version=PROMPT_IR_VERSION,
        system=system,
        context=context,
        instruction=instructions,
        constraints=constraints,
        examples=[],
    )


def _build_system_lines(profile: OmomukiProfile) -> list[str]:
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


def _build_context_lines(profile: OmomukiProfile) -> list[str]:
    lines: list[str] = []
    idx = profile.context_index
    if idx.entrypoint:
        lines.append(f"Context entrypoint: {idx.entrypoint}")
    if idx.handoff:
        lines.append(f"Context handoff: {idx.handoff}")
    return lines


def _build_constraint_lines(profile: OmomukiProfile) -> list[str]:
    response = profile.policy.response
    if response is None:
        return []
    lines: list[str] = []
    if response.avoid:
        lines.append(f"Avoid: {', '.join(response.avoid)}.")
    if response.prefer:
        lines.append(f"Prefer: {', '.join(response.prefer)}.")
    return lines
