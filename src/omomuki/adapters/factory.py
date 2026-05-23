"""Factory for target-specific adapters."""

from omomuki.adapters.base import Adapter
from omomuki.adapters.chatgpt import ChatGPTAdapter
from omomuki.adapters.claude import ClaudeAdapter

_ADAPTERS: dict[str, type[Adapter]] = {
    "chatgpt": ChatGPTAdapter,
    "openai": ChatGPTAdapter,
    "claude": ClaudeAdapter,
    "anthropic": ClaudeAdapter,
}


def get_adapter(target: str) -> Adapter:
    """Return an adapter instance for the given target name."""
    key = target.lower().strip()
    adapter_cls = _ADAPTERS.get(key)
    if adapter_cls is None:
        supported = ", ".join(sorted({k for k in _ADAPTERS if k in ("chatgpt", "claude")}))
        raise ValueError(f"Unknown target: {target}. Supported: {supported}")
    return adapter_cls()
