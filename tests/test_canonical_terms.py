"""Canonical terminology resolution and adapter export tests."""

from pathlib import Path

from sayane.adapters.deepseek import DeepSeekAdapter
from sayane.adapters.gemini import GeminiAdapter
from sayane.core.builder import build_prompt_ir
from sayane.core.canonical_terms import (
    apply_canonical_terms_to_text,
    attach_canonical_terms_to_ir,
    merge_canonical_terms,
)
from sayane.core.loader import load_profile
from sayane.core.models import CanonicalTerm, PromptIR, SayaneProfile, SayaneProjectProfile


def _profile_with_canonical_terms() -> SayaneProfile:
    base = load_profile(Path("examples/profiles/minimal.yaml"))
    base.canonical_terms = [
        CanonicalTerm(
            term="ABC",
            expansion="Approved Base Concept",
            description="A canonical project-specific term used for testing.",
            deprecated=["Alternative Broken Concept"],
            correction_policy="replace_deprecated_with_canonical",
        ),
        CanonicalTerm(
            term="XYZ",
            expansion="Cross Yield Zone",
            deprecated=["legacy-xyz"],
            correction_policy="warn_and_preserve_context",
        ),
    ]
    return base


def test_merge_prefers_project_profile_terms() -> None:
    user = _profile_with_canonical_terms()
    user.canonical_terms = [
        CanonicalTerm(
            term="ABC",
            expansion="Approved Base Concept",
            deprecated=[],
        ),
    ]
    project = SayaneProjectProfile(
        version="0.1.0",
        kind="SayaneProjectProfile",
        canonical_terms=[
            CanonicalTerm(
                term="ABC",
                expansion="Architecture Boundary Contract",
                deprecated=["Alternative Broken Concept"],
            ),
        ],
    )
    merged = merge_canonical_terms(user, project)
    assert len(merged) == 1
    abc = next(t for t in merged if t.term == "ABC")
    assert abc.expansion == "Architecture Boundary Contract"


def test_replace_deprecated_with_canonical() -> None:
    terms = _profile_with_canonical_terms().canonical_terms
    updated, notes, blocked = apply_canonical_terms_to_text(
        "Alternative Broken Concept appears in this draft.",
        terms,
    )
    assert "Alternative Broken Concept" not in updated
    assert "Approved Base Concept" in updated
    assert notes
    assert blocked is False


def test_builder_without_canonical_terms_does_not_expand_abbreviations(
    examples_dir: Path,
) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    ir = build_prompt_ir(profile, profile_root=examples_dir / "profiles")
    assert ir.canonical_terms == []
    joined = "\n".join([*ir.system, *ir.context, *ir.instruction, *ir.constraints])
    assert "Approved Base Concept" not in joined


def test_deepseek_output_reflects_canonical_terms(examples_dir: Path) -> None:
    profile = _profile_with_canonical_terms()
    profile.context_index.entries = []
    ir = build_prompt_ir(
        profile,
        profile_root=examples_dir / "profiles",
        load_context_bodies=False,
    )
    ir.context.append("Alternative Broken Concept appears in old docs.")
    attach_canonical_terms_to_ir(ir, profile.canonical_terms)
    result = DeepSeekAdapter().compile(ir)
    text = result.payload["text"]

    assert "Alternative Broken Concept" not in text
    assert "Approved Base Concept" in text
    assert "## Canonical Terminology" in text or "## 正規語彙" in text
    assert result.payload.get("export_notes")


def test_gemini_and_deepseek_use_different_formats(examples_dir: Path) -> None:
    profile = _profile_with_canonical_terms()
    ir = build_prompt_ir(
        profile,
        instruction="plan",
        profile_root=examples_dir / "profiles",
        load_context_bodies=False,
    )
    attach_canonical_terms_to_ir(ir, profile.canonical_terms)
    gemini = GeminiAdapter().compile(ir)
    deepseek = DeepSeekAdapter().compile(ir)
    assert gemini.format == "gemini_working_memo"
    assert deepseek.format == "deepseek_working_memo"


def test_export_notes_record_replacement() -> None:
    ir = PromptIR(
        system=[],
        context=["Alternative Broken Concept in discussion."],
        instruction=[],
        constraints=[],
    )
    notes = attach_canonical_terms_to_ir(
        ir,
        _profile_with_canonical_terms().canonical_terms,
    )
    assert any("Replaced deprecated" in note for note in notes)
    assert ir.export_notes


def test_warn_and_preserve_context_records_warning_without_replacement() -> None:
    terms = _profile_with_canonical_terms().canonical_terms
    updated, notes, blocked = apply_canonical_terms_to_text("legacy-xyz is referenced.", terms)
    assert "legacy-xyz" in updated
    assert any("warn_and_preserve_context" in note for note in notes)
    assert blocked is False


def test_block_export_requires_user_confirmation(examples_dir: Path) -> None:
    profile = _profile_with_canonical_terms()
    profile.canonical_terms.append(
        CanonicalTerm(
            term="BLOCK",
            expansion="Blocked Export Term",
            deprecated=["forbidden phrase"],
            correction_policy="block_export",
        ),
    )
    ir = build_prompt_ir(
        profile,
        profile_root=examples_dir / "profiles",
        load_context_bodies=False,
    )
    ir.context.append("this includes forbidden phrase in context")
    attach_canonical_terms_to_ir(ir, profile.canonical_terms)
    deepseek = DeepSeekAdapter().compile(ir)
    gemini = GeminiAdapter().compile(ir)

    assert deepseek.payload.get("requires_user_confirmation") is True
    assert gemini.payload.get("requires_user_confirmation") is True
    assert "forbidden phrase" not in str(deepseek.payload)
