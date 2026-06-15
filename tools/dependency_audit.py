#!/usr/bin/env python3
"""Informational dependency boundary audit for Sayane.

This tool implements the first lightweight audit described by ADR 0006.
It is intentionally non-blocking: dependency warnings are reported but do
not fail the process.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

LAYER_RULES = [
    ("src/sayane/bridge/routes/", "bridge_routes"),
    ("src/sayane/cli/", "cli"),
    ("src/sayane/bridge/", "bridge"),
    ("src/sayane/usecases/", "usecases"),
    ("src/sayane/domain/", "domain"),
    ("src/sayane/core/", "core"),
    ("src/sayane/evaluators/", "evaluators"),
    ("src/sayane/vault/", "vault"),
    ("src/sayane/storage/", "storage"),
    ("src/sayane/mcp/", "mcp"),
]

MODULE_LAYER_PREFIXES = [
    ("sayane.bridge.routes", "bridge_routes"),
    ("sayane.cli", "cli"),
    ("sayane.bridge", "bridge"),
    ("sayane.usecases", "usecases"),
    ("sayane.domain", "domain"),
    ("sayane.core", "core"),
    ("sayane.evaluators", "evaluators"),
    ("sayane.vault", "vault"),
    ("sayane.storage", "storage"),
    ("sayane.mcp", "mcp"),
]

SUSPICIOUS_IMPORTS = {
    "domain": {"cli", "bridge", "bridge_routes"},
    "core": {"cli", "bridge_routes"},
    "evaluators": {"cli", "bridge_routes"},
    "usecases": {"cli", "bridge_routes"},
    "bridge_routes": {"cli"},
}

FACADE_LIMITS = {
    "src/sayane/cli/app.py": 200,
    "src/sayane/bridge/app.py": 200,
    "src/sayane/core/export.py": 200,
    "src/sayane/evaluators/capture_parse.py": 200,
    "src/sayane/bridge/candidate_api.py": 300,
}

COMPAT_ALIASES = [
    "_source_excerpt",
    "_capture_preview_text",
    "_candidate_summary",
]


@dataclass(frozen=True)
class ModuleInfo:
    path: Path
    rel_path: str
    module: str
    layer: str
    line_count: int
    imports: tuple[str, ...]


def path_to_module(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    body = rel.removeprefix("src/").removesuffix(".py")
    if body.endswith("/__init__"):
        body = body[: -len("/__init__")]
    return body.replace("/", ".")


def layer_for_path(path: Path, root: Path) -> str:
    rel = path.relative_to(root).as_posix()
    for prefix, layer in LAYER_RULES:
        if rel.startswith(prefix):
            return layer
    return "unknown"


def layer_for_module(module: str) -> str:
    for prefix, layer in MODULE_LAYER_PREFIXES:
        if module == prefix or module.startswith(prefix + "."):
            return layer
    return "unknown"


def extract_imports(source: str) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []

    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(
                alias.name
                for alias in node.names
                if alias.name == "sayane" or alias.name.startswith("sayane.")
            )
        elif isinstance(node, ast.ImportFrom):
            if node.module and (node.module == "sayane" or node.module.startswith("sayane.")):
                imports.append(node.module)
    return sorted(set(imports))


def scan_modules(root: Path) -> list[ModuleInfo]:
    src = root / "src" / "sayane"
    if not src.exists():
        raise FileNotFoundError(f"scan target does not exist: {src}")

    modules: list[ModuleInfo] = []
    for path in sorted(src.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        modules.append(
            ModuleInfo(
                path=path,
                rel_path=path.relative_to(root).as_posix(),
                module=path_to_module(path, root),
                layer=layer_for_path(path, root),
                line_count=len(source.splitlines()),
                imports=tuple(extract_imports(source)),
            )
        )
    return modules


def find_layer_warnings(modules: list[ModuleInfo]) -> list[str]:
    warnings: list[str] = []
    for module in modules:
        targets = SUSPICIOUS_IMPORTS.get(module.layer, set())
        for imported in module.imports:
            imported_layer = layer_for_module(imported)
            if imported_layer in targets:
                warnings.append(
                    f"{module.rel_path}: {module.layer} -> {imported} ({imported_layer})"
                )
    return warnings


def find_facade_warnings(modules: list[ModuleInfo]) -> list[str]:
    by_rel = {module.rel_path: module for module in modules}
    warnings: list[str] = []
    for rel_path, limit in FACADE_LIMITS.items():
        module = by_rel.get(rel_path)
        if module and module.line_count > limit:
            warnings.append(f"{rel_path}: {module.line_count} lines > {limit}")
    return warnings


def find_aliases(modules: list[ModuleInfo]) -> list[str]:
    occurrences: list[str] = []
    for module in modules:
        for line_no, line in enumerate(module.path.read_text(encoding="utf-8").splitlines(), start=1):
            for alias in COMPAT_ALIASES:
                if alias in line:
                    occurrences.append(f"{alias}: {module.rel_path}:{line_no}")
    return occurrences


def render_report(modules: list[ModuleInfo], fmt: str) -> str:
    layer_warnings = find_layer_warnings(modules)
    facade_warnings = find_facade_warnings(modules)
    aliases = find_aliases(modules)
    imports_found = sum(len(module.imports) for module in modules)

    lines = [
        "# Dependency Audit Report",
        "",
        "## Summary",
        "",
        "| Item | Count |",
        "|---|---:|",
        f"| Files scanned | {len(modules)} |",
        f"| Imports found | {imports_found} |",
        f"| Layer warnings | {len(layer_warnings)} |",
        f"| Facade warnings | {len(facade_warnings)} |",
        f"| Compatibility alias occurrences | {len(aliases)} |",
        "",
        "## Layer warnings",
        "",
        *(layer_warnings or ["None."]),
        "",
        "## Facade size warnings",
        "",
        *(facade_warnings or ["None."]),
        "",
        "## Compatibility aliases",
        "",
        *(aliases or ["None."]),
        "",
        "## Notes",
        "",
        "- This audit is informational.",
        "- Warnings do not fail CI.",
        "",
    ]
    markdown = "\n".join(lines)
    if fmt == "markdown":
        return markdown
    return markdown.replace("# ", "").replace("## ", "")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Sayane dependency boundary audit.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--format", choices=("text", "markdown"), default="text")
    parser.add_argument("--output")
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)

    root = Path(args.root).resolve()
    if not root.exists():
        print(f"error: root path does not exist: {root}", file=sys.stderr)
        return 2

    try:
        output = render_report(scan_modules(root), args.format)
    except Exception as exc:
        print(f"error: dependency audit failed: {exc}", file=sys.stderr)
        return 1

    if args.output:
        output_path = Path(args.output)
        if not output_path.is_absolute():
            output_path = root / output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output, encoding="utf-8")
    else:
        print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
