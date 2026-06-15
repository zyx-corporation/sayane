#!/usr/bin/env python3
"""Informational ADR 0004 complexity report.

This script is intentionally dependency-free. It reports warning candidates only;
it must not be used as a hard CI gate until the baseline and thresholds are
reviewed.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

FILE_WARN_LINES = 300
FILE_HIGH_LINES = 500
FUNCTION_WARN_LINES = 50
CLASS_WARN_LINES = 200
CYCLOMATIC_WARN = 10
CYCLOMATIC_HIGH = 20
GOD_FILE_NAMES = {"app.py", "main.py", "service.py", "manager.py", "utils.py", "common.py", "helper.py"}


@dataclass(frozen=True)
class FunctionFinding:
    path: Path
    name: str
    start_line: int
    end_line: int
    line_count: int
    complexity: int


@dataclass(frozen=True)
class ClassFinding:
    path: Path
    name: str
    start_line: int
    end_line: int
    line_count: int


@dataclass
class ModuleReport:
    path: Path
    line_count: int
    is_god_file_name: bool
    functions: list[FunctionFinding] = field(default_factory=list)
    classes: list[ClassFinding] = field(default_factory=list)
    parse_error: str | None = None


def iter_python_files(roots: Iterable[Path]) -> Iterable[Path]:
    for root in roots:
        if root.is_file() and root.suffix == ".py":
            yield root
            continue
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if any(part in {".git", ".venv", "venv", "__pycache__"} for part in path.parts):
                continue
            yield path


def node_end_line(node: ast.AST) -> int | None:
    return getattr(node, "end_lineno", None)


def node_start_line(node: ast.AST) -> int | None:
    return getattr(node, "lineno", None)


def cyclomatic_complexity(node: ast.AST) -> int:
    """Approximate McCabe complexity without external dependencies."""
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.AsyncFor, ast.While, ast.ExceptHandler, ast.With, ast.AsyncWith)):
            score += 1
        elif isinstance(child, ast.BoolOp):
            score += max(0, len(child.values) - 1)
        elif isinstance(child, ast.IfExp):
            score += 1
        elif isinstance(child, ast.Match):
            score += max(1, len(child.cases))
        elif isinstance(child, ast.comprehension):
            score += 1
    return score


def analyze_file(path: Path) -> ModuleReport:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    report = ModuleReport(
        path=path,
        line_count=len(lines),
        is_god_file_name=path.name in GOD_FILE_NAMES,
    )
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as exc:
        report.parse_error = f"{exc.__class__.__name__}: {exc}"
        return report

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node_start_line(node)
            end = node_end_line(node)
            if start is None or end is None:
                continue
            report.functions.append(
                FunctionFinding(
                    path=path,
                    name=node.name,
                    start_line=start,
                    end_line=end,
                    line_count=end - start + 1,
                    complexity=cyclomatic_complexity(node),
                )
            )
        elif isinstance(node, ast.ClassDef):
            start = node_start_line(node)
            end = node_end_line(node)
            if start is None or end is None:
                continue
            report.classes.append(
                ClassFinding(
                    path=path,
                    name=node.name,
                    start_line=start,
                    end_line=end,
                    line_count=end - start + 1,
                )
            )
    return report


def rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def render_report(reports: list[ModuleReport], root: Path) -> str:
    large_files = [r for r in reports if r.line_count >= FILE_WARN_LINES]
    god_files = [r for r in reports if r.is_god_file_name]
    long_functions = [f for r in reports for f in r.functions if f.line_count >= FUNCTION_WARN_LINES]
    long_classes = [c for r in reports for c in r.classes if c.line_count >= CLASS_WARN_LINES]
    complex_functions = [f for r in reports for f in r.functions if f.complexity >= CYCLOMATIC_WARN]
    parse_errors = [r for r in reports if r.parse_error]

    output: list[str] = []
    output.append("# ADR 0004 Complexity Report")
    output.append("")
    output.append("Informational only. This report does not imply CI failure.")
    output.append("")
    output.append("## Summary")
    output.append("")
    output.append(f"- Python files scanned: {len(reports)}")
    output.append(f"- Files >= {FILE_WARN_LINES} lines: {len(large_files)}")
    output.append(f"- God-file names: {len(god_files)}")
    output.append(f"- Functions >= {FUNCTION_WARN_LINES} lines: {len(long_functions)}")
    output.append(f"- Classes >= {CLASS_WARN_LINES} lines: {len(long_classes)}")
    output.append(f"- Functions complexity >= {CYCLOMATIC_WARN}: {len(complex_functions)}")
    output.append(f"- Parse errors: {len(parse_errors)}")
    output.append("")

    if large_files:
        output.append("## Large files")
        output.append("")
        for report in sorted(large_files, key=lambda r: r.line_count, reverse=True):
            marker = "HIGH" if report.line_count >= FILE_HIGH_LINES else "WARN"
            output.append(f"- {marker}: {rel(report.path, root)} ({report.line_count} lines)")
        output.append("")

    if god_files:
        output.append("## God-file name candidates")
        output.append("")
        for report in sorted(god_files, key=lambda r: str(r.path)):
            output.append(f"- {rel(report.path, root)} ({report.line_count} lines)")
        output.append("")

    if long_functions:
        output.append("## Long functions")
        output.append("")
        for item in sorted(long_functions, key=lambda f: f.line_count, reverse=True):
            output.append(
                f"- {rel(item.path, root)}::{item.name} "
                f"L{item.start_line}-L{item.end_line} ({item.line_count} lines, CC={item.complexity})"
            )
        output.append("")

    if complex_functions:
        output.append("## Complex functions")
        output.append("")
        for item in sorted(complex_functions, key=lambda f: f.complexity, reverse=True):
            marker = "HIGH" if item.complexity >= CYCLOMATIC_HIGH else "WARN"
            output.append(
                f"- {marker}: {rel(item.path, root)}::{item.name} "
                f"L{item.start_line}-L{item.end_line} (CC={item.complexity}, {item.line_count} lines)"
            )
        output.append("")

    if long_classes:
        output.append("## Long classes")
        output.append("")
        for item in sorted(long_classes, key=lambda c: c.line_count, reverse=True):
            output.append(
                f"- {rel(item.path, root)}::{item.name} "
                f"L{item.start_line}-L{item.end_line} ({item.line_count} lines)"
            )
        output.append("")

    if parse_errors:
        output.append("## Parse errors")
        output.append("")
        for report in parse_errors:
            output.append(f"- {rel(report.path, root)}: {report.parse_error}")
        output.append("")

    return "\n".join(output).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate an informational ADR 0004 complexity report.")
    parser.add_argument(
        "paths",
        nargs="*",
        default=["src", "tests"],
        help="Files or directories to scan. Defaults to src and tests.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path.cwd()
    roots = [Path(path) for path in args.paths]
    reports = [analyze_file(path) for path in iter_python_files(roots)]
    print(render_report(reports, root), end="")


if __name__ == "__main__":
    main()
