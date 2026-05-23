from pathlib import Path

from omomuki.core.builder import build_prompt_ir
from omomuki.core.loader import load_profile
from omomuki.core.models import PromptIR


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
