"""Sayane MCP Server (stdio) — read-only tools."""

import json

from mcp.server.fastmcp import FastMCP

from sayane.mcp.operations import get_operations

mcp = FastMCP(
    "Sayane",
    instructions=(
        "Sayane persona and context tools. Lists profiles, compiles prompts, "
        "and manages candidate captures (evaluate / approve / reject). "
        "approve_candidate merges into the profile only when explicitly called; "
        "use force_critical only after reviewing RDE classification."
    ),
)


def _dump(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


@mcp.tool()
def list_profiles() -> str:
    """List available Sayane profiles in the local store."""
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
    """Compile Sayane Profile to a target LLM request shape (chatgpt or claude)."""
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
    """List candidate captures (not necessarily merged into profile)."""
    return _dump(get_operations().list_candidate_updates())


@mcp.tool()
def show_candidate(candidate_id: str) -> str:
    """Show full candidate record by id."""
    try:
        return _dump(get_operations().show_candidate(candidate_id))
    except FileNotFoundError as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def evaluate_candidate(candidate_id: str, level: int = 1) -> str:
    """Run RDE/UIB evaluation (level 1 heuristic; 2/3 optional LLM judge)."""
    try:
        return _dump(get_operations().evaluate_candidate(candidate_id, level=level))
    except FileNotFoundError as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def approve_candidate(candidate_id: str, force_critical: bool = False) -> str:
    """Approve candidate and merge into profile. Requires prior evaluation."""
    try:
        return _dump(
            get_operations().approve_candidate(
                candidate_id,
                force_critical=force_critical,
            ),
        )
    except (FileNotFoundError, ValueError) as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def reject_candidate(candidate_id: str, reason: str | None = None) -> str:
    """Reject candidate without merging into profile."""
    try:
        return _dump(get_operations().reject_candidate(candidate_id, reason=reason))
    except FileNotFoundError as exc:
        return _dump({"error": str(exc)})


@mcp.tool()
def diff_candidate(candidate_id: str) -> str:
    """Rule-based diff between candidate proposal and current profile."""
    try:
        return _dump(get_operations().diff_candidate(candidate_id))
    except FileNotFoundError as exc:
        return _dump({"error": str(exc)})


def run_stdio() -> None:
    """Run MCP server on stdio transport (Cursor, Claude Desktop, Cline, etc.)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    run_stdio()
