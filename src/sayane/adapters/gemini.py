"""Google Gemini generateContent adapter."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.core.models import PromptIR


class GeminiAdapter(Adapter):
    """Compile Prompt IR to Gemini API generateContent shape."""

    @property
    def target(self) -> str:
        return "gemini"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        system_content = join_sections([ir.system, ir.constraints])
        user_content = join_sections([ir.context, ir.instruction])

        payload: dict = {
            "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        }
        if system_content.strip():
            payload["system_instruction"] = {"parts": [{"text": system_content}]}

        return CompiledPrompt(
            target=self.target,
            format="gemini_generate_content",
            payload=payload,
        )
