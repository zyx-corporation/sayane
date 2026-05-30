"""Factory for target-specific adapters."""

from sayane.adapters.base import Adapter
from sayane.adapters.chatgpt import ChatGPTAdapter
from sayane.adapters.claude import ClaudeAdapter
from sayane.adapters.deepseek import DeepSeekAdapter
from sayane.adapters.gemini import GeminiAdapter
from sayane.adapters.local_openwebui import LocalOpenWebUIAdapter

_ADAPTERS: dict[str, type[Adapter]] = {
    "chatgpt": ChatGPTAdapter,
    "openai": ChatGPTAdapter,
    "claude": ClaudeAdapter,
    "anthropic": ClaudeAdapter,
    "gemini": GeminiAdapter,
    "google": GeminiAdapter,
    "deepseek": DeepSeekAdapter,
    "local-openwebui": LocalOpenWebUIAdapter,
    "openwebui": LocalOpenWebUIAdapter,
}

_PUBLIC_TARGETS = ("chatgpt", "claude", "gemini", "deepseek", "local-openwebui")


def get_adapter(target: str) -> Adapter:
    """Return an adapter instance for the given target name."""
    key = target.lower().strip()
    adapter_cls = _ADAPTERS.get(key)
    if adapter_cls is None:
        supported = ", ".join(sorted(_PUBLIC_TARGETS))
        raise ValueError(f"Unknown target: {target}. Supported: {supported}")
    return adapter_cls()
