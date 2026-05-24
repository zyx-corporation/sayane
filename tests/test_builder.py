from pathlib import Path

from sayane.core.builder import build_prompt_ir
from sayane.core.loader import load_profile
from sayane.core.models import PromptIR


def test_build_prompt_ir_from_minimal_profile(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    ir = build_prompt_ir(profile)

    assert isinstance(ir, PromptIR)
    assert ir.kind == "PromptIR"
    assert any("Example User" in line for line in ir.system)
    assert any("human dignity" in line for line in ir.system)
    assert any("context/MyContext.md" in line for line in ir.context)
    assert any("unsupported overclaiming" in line for line in ir.constraints)


def test_build_prompt_ir_with_instruction(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    ir = build_prompt_ir(profile, instruction="Summarize the handoff document.")

    assert any("Summarize" in line for line in ir.instruction)


def test_build_prompt_ir_loads_context_bodies(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    profile = load_profile(profile_path)
    ir = build_prompt_ir(
        profile,
        profile_root=profile_path.parent,
        load_context_bodies=True,
    )
    joined = "\n".join(ir.context)
    assert "Example context" in joined or "Handoff notes" in joined
