"""T-RDE tests for Signed Export Package (Phase 17)."""
import json
import tempfile
from pathlib import Path

from sayane.core.export_package import (
    build_package_manifest,
    create_package,
    inspect_package,
    verify_package,
)


def test_build_package_manifest_hashes_artifacts():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        manifest = build_package_manifest({"bundle": f1})
        assert len(manifest["artifacts"]) == 1
        assert manifest["artifacts"][0]["hash"]["value"]


def test_package_create_generates_manifest():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        manifest = create_package(out, {"bundle": f1})
        assert (out / "manifest.json").exists()
        assert manifest["schema_version"] == "sayane-export-package-v1"


def test_package_inspect_lists_artifacts():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        inspected = inspect_package(out)
        assert inspected is not None
        assert len(inspected["artifacts"]) == 1


def test_package_verify_success():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        result = verify_package(out)
        assert result["status"] in ("VERIFIED", "VERIFIED_WITH_WARNINGS")
        assert len(result["errors"]) == 0


def test_package_verify_detects_artifact_tampering():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        # Tamper
        (out / "artifacts" / "bundle.yml").write_text("identity:\n  name: Hacked\n")
        result = verify_package(out)
        assert result["status"] == "FAILED"


def test_package_verify_detects_missing_artifact():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        f2 = td / "report.json"
        f2.write_text('{"test": true}')
        out = td / "pkg"
        create_package(out, {"bundle": f1, "report": f2})
        # Delete one artifact
        (out / "artifacts" / "bundle.yml").unlink()
        result = verify_package(out)
        assert result["status"] == "FAILED"


def test_package_readme_contains_boundary_language():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        readme = (out / "README.md").read_text()
        assert "does not prove" in readme
        assert "not imply automatic acceptance" in readme


def test_package_manifest_not_tampered_after_inspect():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        manifest = create_package(out, {"bundle": f1})
        inspected = inspect_package(out)
        assert inspected["package_id"] == manifest["package_id"]
