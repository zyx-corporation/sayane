"""Omomuki MCP Server (stdio) — read-only tools."""

import json

from mcp.server.fastmcp import FastMCP

from omomuki.mcp.operations import get_operations

mcp = FastMCP(
    "Omomuki",
    instructions=(
        "Read-only Omomuki persona and context tools. "
        "Lists profiles, inspects summaries, compiles prompts, and lists candidate "
        "captures. Does not merge or modify profiles."
    ),
)


def _dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def list_profiles() -> str:
    """List available Omomuki profiles in the local store."""
    return _dump(get_operations().list_profiles())


@mcp.tool()
def inspect_profile(profile_id: str = "default") -> str:
    """Return a summary of the given profile (no full secrets dump)."""
    try:
        return _dump(get_operations().inspect_profile(profile_id=profile_id))
    except FileNotFoundError as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def compile_prompt(
    target: str,
    profile_id: str = "default",
    instruction: str | None = None,
) -> str:
    """Compile Omomuki Profile to a target LLM request shape (chatgpt or claude)."""
    try:
        return _dump(
            get_operations().compile_prompt(
                target=target,
                profile_id=profile_id,
                instruction=instruction,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def generate_context_packet(
    target: str,
    profile_id: str = "default",
    instruction: str | None = None,
) -> str:
    """Generate a context packet for external LLM clients (same as compile_prompt)."""
    try:
        return _dump(
            get_operations().generate_context_packet(
                target=target,
                profile_id=profile_id,
                instruction=instruction,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def list_candidate_updates() -> str:
    """List pending candidate captures (not merged into profile)."""
    return _dump(get_operations().list_candidate_updates())


def run_stdio() -> None:
    """Run MCP server on stdio transport (Cursor, Claude Desktop, Cline, etc.)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
