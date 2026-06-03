"""OpenAI Chat Completions adapter."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.adapters.working_memo import detect_language
from sayane.core.canonical_terms import format_canonical_terms_section
from sayane.core.models import PromptIR


class ChatGPTAdapter(Adapter):
    """Compile Prompt IR to OpenAI-style chat messages."""

    @property
    def target(self) -> str:
        return "chatgpt"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        if ir.export_blocked:
            return CompiledPrompt(
                target=self.target,
                format="openai_chat",
                payload={
                    "requires_user_confirmation": True,
                    "message": (
                        "Export blocked by canonical terminology policy. "
                        "Review export_notes and confirm before proceeding."
                    ),
                    "export_notes": list(ir.export_notes),
                    "messages": [],
                },
            )

        system_content = join_sections([ir.system])
        if ir.canonical_terms:
            canonical = format_canonical_terms_section(
                ir.canonical_terms,
                lang=detect_language(ir),
            )
            system_content = f"{system_content}\n\n{canonical}".strip()
        user_content = join_sections([ir.context, ir.instruction, ir.constraints])

        messages: list[dict[str, str]] = [{"role": "system", "content": system_content}]
        if user_content.strip():
            messages.append({"role": "user", "content": user_content})

        return CompiledPrompt(
            target=self.target,
            format="openai_chat",
            payload={"messages": messages},
        )
