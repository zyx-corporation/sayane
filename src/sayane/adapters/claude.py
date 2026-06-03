"""Anthropic Messages API adapter."""

from sayane.adapters.base import Adapter, CompiledPrompt, join_sections
from sayane.adapters.working_memo import detect_language
from sayane.core.canonical_terms import format_canonical_terms_section
from sayane.core.models import PromptIR


class ClaudeAdapter(Adapter):
    """Compile Prompt IR to Anthropic-style system + messages."""

    @property
    def target(self) -> str:
        return "claude"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        if ir.export_blocked:
            return CompiledPrompt(
                target=self.target,
                format="anthropic_messages",
                payload={
                    "requires_user_confirmation": True,
                    "message": (
                        "Export blocked by canonical terminology policy. "
                        "Review export_notes and confirm before proceeding."
                    ),
                    "export_notes": list(ir.export_notes),
                    "system": "",
                    "messages": [],
                },
            )

        system_content = join_sections([ir.system, ir.constraints])
        if ir.canonical_terms:
            canonical = format_canonical_terms_section(
                ir.canonical_terms,
                lang=detect_language(ir),
            )
            system_content = f"{system_content}\n\n{canonical}".strip()
        user_content = join_sections([ir.context, ir.instruction])

        return CompiledPrompt(
            target=self.target,
            format="anthropic_messages",
            payload={
                "system": system_content,
                "messages": [{"role": "user", "content": user_content}],
            },
        )
