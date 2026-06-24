"""MCP package exports with lazy server loading."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["McpOperations", "get_operations", "mcp", "run_stdio"]


def __getattr__(name: str) -> Any:
    if name in {"McpOperations", "get_operations"}:
        module = import_module("sayane.mcp.operations")
        return getattr(module, name)
    if name in {"mcp", "run_stdio"}:
        module = import_module("sayane.mcp.server")
        return getattr(module, name)
    raise AttributeError(name)
