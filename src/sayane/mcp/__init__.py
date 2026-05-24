"""MCP Server — read-only access for AI clients."""

from sayane.mcp.operations import McpOperations, get_operations
from sayane.mcp.server import mcp, run_stdio

__all__ = ["McpOperations", "get_operations", "mcp", "run_stdio"]
