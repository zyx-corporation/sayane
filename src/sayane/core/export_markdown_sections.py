"""Additional markdown section renderer helpers."""

from __future__ import annotations

from typing import Any


def append_philosophical_stance(lines: list[str], data: dict[str, Any]) -> None:
    values = data.get("values")
    if not isinstance(values, dict):
        return
    core = values.get("core", [])
    if not core:
        return
    lines.append("## Philosophical Stance")
    lines.append("")
    for index, axiom in enumerate(core, start=1):
        lines.append(f"### Axiom {index}")
        lines.append("")
        lines.append("Quote:")
        lines.append("")
        lines.append(f"> {axiom}")
        lines.append("")
        lines.append("Interpretation: not provided")
        lines.append("")


def append_knowledge_projects_terms(lines: list[str], data: dict[str, Any]) -> None:
    knowledge = data.get("knowledge")
    if isinstance(knowledge, dict) and knowledge.get("concepts"):
        lines.append("## Key Concepts")
        lines.append("")
        for concept in knowledge["concepts"]:
            lines.append(f"- {concept}")
        lines.append("")
    projects = data.get("major_projects", [])
    if projects:
        lines.append("## Projects")
        lines.append("")
        for project in projects:
            if isinstance(project, dict):
                name = project.get("name", "")
                summary = project.get("summary", "")
                lines.append(f"- **{name}**: {summary}" if summary else f"- {name}")
        lines.append("")
    terms = data.get("important_terms", [])
    if terms:
        lines.append("## Important Terms")
        lines.append("")
        for term in terms:
            lines.append(f"- {term}")
        lines.append("")


def append_principles(lines: list[str], data: dict[str, Any]) -> None:
    knowledge = data.get("knowledge")
    if not isinstance(knowledge, dict) or not knowledge.get("concepts"):
        return
    lines.append("## Principles")
    lines.append("")
    for concept in knowledge["concepts"]:
        lines.append(f"- {concept}")
    lines.append("")


def append_execution_context(lines: list[str], data: dict[str, Any]) -> None:
    projects = data.get("major_projects", [])
    cm = data.get("communication_mode")
    if not projects and not isinstance(cm, dict):
        return
    lines.append("## Execution Context")
    lines.append("")
    if projects:
        lines.append("### Projects")
        lines.append("")
        for project in projects:
            if isinstance(project, dict):
                name = project.get("name", "")
                summary = project.get("summary", "")
                lines.append(f"- **{name}**: {summary}" if summary else f"- {name}")
        lines.append("")
