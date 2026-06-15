import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools" / "dependency_audit.py"
spec = importlib.util.spec_from_file_location("dependency_audit", SCRIPT)
dependency_audit = importlib.util.module_from_spec(spec)
assert spec.loader is not None
sys.modules["dependency_audit"] = dependency_audit
spec.loader.exec_module(dependency_audit)


def write_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def make_repo(tmp_path: Path) -> Path:
    root = tmp_path
    write_file(root / "src" / "sayane" / "__init__.py", "")
    return root


def test_path_to_module_regular_file(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "core" / "export.py"
    write_file(path, "")
    assert dependency_audit.path_to_module(path, root) == "sayane.core.export"


def test_path_to_module_init_file(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "core" / "__init__.py"
    write_file(path, "")
    assert dependency_audit.path_to_module(path, root) == "sayane.core"


def test_layer_for_path_uses_specific_bridge_routes_first(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "bridge" / "routes" / "candidates.py"
    write_file(path, "")
    assert dependency_audit.layer_for_path(path, root) == "bridge_routes"


def test_extract_imports_from_ast() -> None:
    source = """
import os
import sayane.core.export
from sayane.domain import candidate_policy
from sayane.bridge.routes import candidates
"""
    imports = dependency_audit.extract_imports(source)
    assert "sayane.core.export" in imports
    assert "sayane.domain" in imports
    assert "sayane.bridge.routes" in imports
    assert "os" not in imports


def test_detect_layer_warning_for_domain_importing_bridge(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "domain" / "candidate_policy.py"
    write_file(path, "from sayane.bridge import candidate_presenter\n")
    modules = dependency_audit.scan_modules(root)
    warnings = dependency_audit.find_layer_warnings(modules)
    assert len(warnings) == 1
    assert "domain -> sayane.bridge" in warnings[0]


def test_no_layer_warning_for_bridge_route_importing_usecase(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "bridge" / "routes" / "candidates.py"
    write_file(path, "from sayane.usecases import candidate_lifecycle\n")
    modules = dependency_audit.scan_modules(root)
    assert dependency_audit.find_layer_warnings(modules) == []


def test_facade_warning(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "bridge" / "candidate_api.py"
    write_file(path, "\n".join(["pass"] * 301))
    modules = dependency_audit.scan_modules(root)
    warnings = dependency_audit.find_facade_warnings(modules)
    assert warnings == ["src/sayane/bridge/candidate_api.py: 301 lines > 300"]


def test_alias_occurrence_detection(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "bridge" / "candidate_api.py"
    write_file(path, "_capture_preview_text = lambda x: x\n")
    modules = dependency_audit.scan_modules(root)
    assert dependency_audit.find_aliases(modules) == [
        "_capture_preview_text: src/sayane/bridge/candidate_api.py:1"
    ]


def test_markdown_report_contains_summary(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    modules = dependency_audit.scan_modules(root)
    rendered = dependency_audit.render_report(modules, "markdown")
    assert "# Dependency Audit Report" in rendered
    assert "| Files scanned | 1 |" in rendered
    assert "Warnings do not fail CI" in rendered


def test_main_exits_zero_with_warnings(tmp_path: Path) -> None:
    root = make_repo(tmp_path)
    path = root / "src" / "sayane" / "domain" / "candidate_policy.py"
    write_file(path, "from sayane.bridge import candidate_presenter\n")
    output = root / "dependency-audit.md"
    exit_code = dependency_audit.main([
        "--root", str(root), "--format", "markdown", "--output", str(output)
    ])
    assert exit_code == 0
    assert output.exists()
    assert "Layer warnings" in output.read_text(encoding="utf-8")
