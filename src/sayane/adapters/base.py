"""Adapter base types."""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from sayane.core.models import PromptIR


class CompiledPrompt(BaseModel):
    """LLM-specific compiled output from Prompt IR."""

    target: str
    format: str
    payload: dict[str, Any]


class Adapter(ABC):
    """Convert Prompt IR into a target LLM request shape."""

    @property
    @abstractmethod
    def target(self) -> str:
        """Adapter target identifier (e.g. chatgpt, claude)."""

    @abstractmethod
    def compile(self, ir: PromptIR) -> CompiledPrompt:
        """Compile Prompt IR to target-specific payload."""


def join_sections(sections: list[list[str]]) -> str:
    """Join IR section lists into a single message block."""
    parts: list[str] = []
    for block in sections:
        if block:
            parts.append("\n".join(block))
    return "\n\n".join(parts)
