"""DeepSeek API adapter (OpenAI-compatible chat messages)."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.core.models import PromptIR


class DeepSeekAdapter(Adapter):
    """Compile Prompt IR to DeepSeek / OpenAI-compatible chat messages."""

    @property
    def target(self) -> str:
        return "deepseek"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        system_content = join_sections([ir.system])
        user_content = join_sections([ir.context, ir.instruction, ir.constraints])

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        if user_content.strip():
            messages.append({"role": "user", "content": user_content})

        return CompiledPrompt(
            target=self.target,
            format="openai_chat",
            payload={"messages": messages},
        )
