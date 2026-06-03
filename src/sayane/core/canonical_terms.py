"""Profile-defined canonical terminology helpers (no hardcoded theory terms)."""

from __future__ import annotations

from sayane.core.models import (
    CanonicalTerm,
    CanonicalTermRef,
    PromptIR,
    SayaneProfile,
    SayaneProjectProfile,
)


def merge_canonical_terms(
    user_profile: SayaneProfile,
    project_profile: SayaneProjectProfile | None,
) -> list[CanonicalTerm]:
    """Merge terms: project profile overrides user profile per term key."""
    by_term: dict[str, CanonicalTerm] = {
        t.term.strip().lower(): t
        for t in user_profile.canonical_terms
        if t.term.strip()
    }
    if project_profile:
        for term in project_profile.canonical_terms:
            if term.term.strip():
                by_term[term.term.strip().lower()] = term
    return list(by_term.values())


def apply_canonical_terms_to_text(
    text: str,
    terms: list[CanonicalTerm],
) -> tuple[str, list[str], bool]:
    """Apply correction policies to a single text blob."""
    notes: list[str] = []
    out = text
    blocked = False
    replacements: list[tuple[str, str, CanonicalTerm]] = []
    for term in terms:
        for deprecated in term.deprecated:
            if deprecated.strip():
                replacements.append((deprecated, term.expansion, term))
    replacements.sort(key=lambda item: len(item[0]), reverse=True)

    for deprecated, expansion, term in replacements:
        if deprecated not in out:
            continue
        policy = term.correction_policy
        if policy == "replace_deprecated_with_canonical":
            out = out.replace(deprecated, expansion)
            notes.append(
                f"Replaced deprecated '{deprecated}' with canonical expansion "
                f"for {term.term}.",
            )
        elif policy == "warn_and_preserve_context":
            notes.append(
                f"Deprecated term '{deprecated}' present for {term.term}; "
                "left unchanged (warn_and_preserve_context).",
            )
        elif policy == "block_export":
            notes.append(
                f"Blocked export due to deprecated term policy for {term.term}.",
            )
            blocked = True
    return out, notes, blocked


def apply_canonical_terms_to_ir(
    ir: PromptIR,
    terms: list[CanonicalTerm],
) -> tuple[list[str], bool]:
    """Apply canonical term policies to all Prompt IR text sections."""
    if not terms:
        return [], False

    all_notes: list[str] = []
    blocked = False

    def _apply_list(lines: list[str]) -> None:
        nonlocal blocked
        for index, line in enumerate(lines):
            updated, notes, is_blocked = apply_canonical_terms_to_text(line, terms)
            lines[index] = updated
            all_notes.extend(notes)
            blocked = blocked or is_blocked

    _apply_list(ir.system)
    _apply_list(ir.context)
    _apply_list(ir.instruction)
    _apply_list(ir.constraints)
    return all_notes, blocked


def attach_canonical_terms_to_ir(
    ir: PromptIR,
    terms: list[CanonicalTerm],
) -> list[str]:
    """Apply policies and attach resolved terms + export notes to Prompt IR."""
    notes, blocked = apply_canonical_terms_to_ir(ir, terms)
    ir.canonical_terms = [
        CanonicalTermRef(
            term=t.term,
            expansion=t.expansion,
            description=t.description,
            deprecated=list(t.deprecated),
        )
        for t in terms
    ]
    ir.export_notes = notes
    ir.export_blocked = blocked
    return notes


def format_canonical_terms_section(
    terms: list[CanonicalTermRef],
    *,
    lang: str,
    include_deprecated_values: bool = True,
) -> str:
    """Render canonical terminology block for adapter output."""
    if not terms:
        return ""
    header = "## 正規語彙" if lang == "ja" else "## Canonical Terminology"
    lines = [header, ""]
    for term in terms:
        lines.append(f"- {term.term}: {term.expansion}")
        if term.description:
            lines.append(f"  - {term.description}")
        if term.deprecated:
            if lang == "ja":
                if include_deprecated_values:
                    joined = ", ".join(term.deprecated)
                    lines.append(
                        f"  - deprecated（このProfileでは使用しない）: {joined}",
                    )
                else:
                    lines.append("  - deprecated（このProfileでは使用しない）")
            else:
                if include_deprecated_values:
                    joined = ", ".join(term.deprecated)
                    lines.append(f"  - deprecated in this profile: {joined}")
                else:
                    lines.append("  - deprecated in this profile")
    return "\n".join(lines)
