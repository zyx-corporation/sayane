from pathlib import Path

from omomuki.adapters.chatgpt import ChatGPTAdapter
from omomuki.adapters.claude import ClaudeAdapter
from omomuki.adapters.factory import get_adapter
from omomuki.core.builder import build_prompt_ir
from omomuki.core.loader import load_profile


def _minimal_ir(examples_dir: Path):
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    return build_prompt_ir(profile, instruction="Help me plan next steps.")


def test_chatgpt_adapter_produces_openai_messages(examples_dir: Path) -> None:
    ir = _minimal_ir(examples_dir)
    result = ChatGPTAdapter().compile(ir)

    assert result.target == "chatgpt"
    assert result.format == "openai_chat"
    messages = result.payload["messages"]
    assert messages[0]["role"] == "system"
    assert messages[-1]["role"] == "user"
    assert "Example User" in messages[0]["content"]


def test_claude_adapter_produces_anthropic_shape(examples_dir: Path) -> None:
    ir = _minimal_ir(examples_dir)
    result = ClaudeAdapter().compile(ir)

    assert result.target == "claude"
    assert result.format == "anthropic_messages"
    assert "system" in result.payload
    assert result.payload["messages"][0]["role"] == "user"
    assert "Example User" in result.payload["system"]


def test_factory_resolves_targets(examples_dir: Path) -> None:
    ir = _minimal_ir(examples_dir)
    assert get_adapter("chatgpt").compile(ir).target == "chatgpt"
    assert get_adapter("claude").compile(ir).target == "claude"
    assert get_adapter("openai").compile(ir).target == "chatgpt"


def test_factory_rejects_unknown_target() -> None:
    import pytest

    with pytest.raises(ValueError, match="Unknown target"):
        get_adapter("gemini")
