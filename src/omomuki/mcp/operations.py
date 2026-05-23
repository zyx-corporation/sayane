"""Shared read-only operations for MCP tools and CLI."""

from typing import Any

from omomuki.bridge.config import BridgeConfig
from omomuki.bridge.models import CompileRequest
from omomuki.bridge.service import compile_prompt, list_profiles, resolve_profile_path
from omomuki.core.loader import load_profile

SUPPORTED_TARGETS = ("chatgpt", "claude", "openai", "anthropic")


class McpOperations:
    """Read-only Omomuki operations exposed via MCP and CLI."""

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
            raise ValueError("Use omomuki export --format markdown for markdown output")
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
        from omomuki.storage.candidates import list_candidate_ids, load_candidate

        results: list[dict[str, Any]] = []
        for cid in list_candidate_ids(self.config):
            try:
                c = load_candidate(self.config, cid)
                preview = c.content if len(c.content) <= 200 else c.content[:200] + "..."
                results.append(
                    {
                        "id": c.id,
                        "status": c.status,
                        "source": c.source.type,
                        "source_url": c.source.uri,
                        "captured_at": c.source.captured_at.isoformat(),
                        "rde_class": c.evaluation.rde_class if c.evaluation else None,
                        "content_preview": preview,
                    },
                )
            except Exception:
                continue
        return results


def get_operations(config: BridgeConfig | None = None) -> McpOperations:
    return McpOperations(config=config)
