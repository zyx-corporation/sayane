"""Anthropic Messages API adapter."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.core.models import PromptIR


class ClaudeAdapter(Adapter):
    """Compile Prompt IR to Anthropic-style system + messages."""

    @property
    def target(self) -> str:
        return "claude"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        system_content = join_sections([ir.system, ir.constraints])
        user_content = join_sections([ir.context, ir.instruction])

        return CompiledPrompt(
            target=self.target,
            format="anthropic_messages",
            payload={
                "system": system_content,
                "messages": [{"role": "user", "content": user_content}],
            },
        )
