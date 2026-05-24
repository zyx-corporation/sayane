"""Shared read-only operations for MCP tools and CLI."""

from typing import Any

from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CompileRequest
from sayane.bridge.service import compile_prompt, list_profiles, resolve_profile_path
from sayane.core.loader import load_profile

SUPPORTED_TARGETS = ("chatgpt", "claude", "openai", "anthropic")


class McpOperations:
    """Read-only Sayane operations exposed via MCP and CLI."""

    def __init__(self, config: BridgeConfig | None = None) -> None:
        self.config = config or BridgeConfig()

    def list_profiles(self) -> list[dict[str, Any]]:
        return [p.model_dump() for p in list_profiles(self.config)]

    def inspect_profile(self, profile_id: str = "default") -> dict[str, Any]:
        path = resolve_profile_path(self.config, profile_id)
        profile = load_profile(path)
        knowledge = profile.knowledge
        return {
            "profile_id": profile_id,
            "path": str(path),
            "version": profile.version,
            "kind": profile.kind,
            "identity": {
                "name": profile.identity.name,
                "preferred_name": profile.identity.preferred_name,
                "roles": profile.identity.roles,
            },
            "voice": {
                "default_language": profile.voice.default_language,
                "tone": profile.voice.tone,
            },
            "values_count": len(profile.values.core),
            "concepts_count": len(knowledge.concepts) if knowledge else 0,
            "context_index": {
                "entrypoint": profile.context_index.entrypoint,
                "handoff": profile.context_index.handoff,
            },
            "read_only": True,
        }

    def compile_prompt(
        self,
        target: str,
        profile_id: str = "default",
        instruction: str | None = None,
    ) -> dict[str, Any]:
        if target.lower() not in SUPPORTED_TARGETS and target.lower() != "markdown":
            raise ValueError(
                f"Unsupported target: {target}. "
                "Supported: chatgpt, claude (markdown via export only)",
            )
        if target.lower() == "markdown":
            raise ValueError("Use sayane export --format markdown for markdown output")
        request = CompileRequest(
            target=target,
            profile_id=profile_id,
            instruction=instruction,
        )
        return compile_prompt(self.config, request).model_dump()

    def generate_context_packet(
        self,
        target: str,
        profile_id: str = "default",
        instruction: str | None = None,
    ) -> dict[str, Any]:
        """Alias for compile_prompt — context packet for LLM clients."""
        return self.compile_prompt(target=target, profile_id=profile_id, instruction=instruction)

    def list_candidate_updates(self) -> list[dict[str, Any]]:
        from sayane.bridge.candidate_api import list_candidates

        return list_candidates(self.config)

    def show_candidate(self, candidate_id: str) -> dict[str, Any]:
        from sayane.bridge.candidate_api import get_candidate

        return get_candidate(self.config, candidate_id)

    def evaluate_candidate(self, candidate_id: str, level: int = 1) -> dict[str, Any]:
        from sayane.bridge.candidate_api import post_evaluate

        return post_evaluate(self.config, candidate_id, level=level)

    def approve_candidate(
        self,
        candidate_id: str,
        *,
        force_critical: bool = False,
    ) -> dict[str, Any]:
        from sayane.bridge.candidate_api import post_approve

        return post_approve(self.config, candidate_id, force_critical=force_critical)

    def reject_candidate(
        self,
        candidate_id: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        from sayane.bridge.candidate_api import post_reject

        return post_reject(self.config, candidate_id, reason=reason)

    def diff_candidate(self, candidate_id: str) -> dict[str, Any]:
        from sayane.bridge.candidate_api import get_diff

        return get_diff(self.config, candidate_id)


def get_operations(config: BridgeConfig | None = None) -> McpOperations:
    return McpOperations(config=config)
