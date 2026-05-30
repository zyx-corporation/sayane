"""Open WebUI adapter (local OpenAI-compatible chat UI)."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.core.models import PromptIR


class LocalOpenWebUIAdapter(Adapter):
    """Compile Prompt IR for Open WebUI (OpenAI-compatible chat messages)."""

    @property
    def target(self) -> str:
        return "local-openwebui"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        system_content = join_sections([ir.system, ir.constraints])
        user_content = join_sections([ir.context, ir.instruction])

        messages: list[dict[str, str]] = []
        if system_content.strip():
            messages.append({"role": "system", "content": system_content})
        if user_content.strip():
            messages.append({"role": "user", "content": user_content})
        if not messages:
            messages.append({"role": "user", "content": ""})

        return CompiledPrompt(
            target=self.target,
            format="openai_chat",
            payload={"messages": messages},
        )
