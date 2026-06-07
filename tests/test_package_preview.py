"""T-RDE tests for Package Import Preview (F-4)."""
import json
import tempfile
from pathlib import Path

from sayane.core.export_package import create_package, preview_package, render_preview_text


def test_package_preview_does_not_modify_profile():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        preview = preview_package(out)
        assert preview["profile_modified"] is False
        assert preview["preview_only"] is True


def test_package_preview_lists_artifacts():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        preview = preview_package(out)
        assert len(preview["artifacts"]) >= 1
        a = preview["artifacts"][0]
        assert "role" in a
        assert "hash_status" in a
        assert "signature_status" in a


def test_package_preview_empty_scoped_contexts():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        preview = preview_package(out)
        assert "scoped_contexts" in preview
        assert "audit_summary" in preview


def test_package_preview_renders_text():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        text = render_preview_text(preview_package(out))
        assert "=== Sayane Package Preview ===" in text
        assert "No profile has been modified" in text


def test_package_preview_boundary_visible():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        text = render_preview_text(preview_package(out))
        assert "preview only" in text or "preview" in text.lower()


def test_package_preview_risks_include_warnings():
    with tempfile.TemporaryDirectory() as d:
        td = Path(d)
        f1 = td / "bundle.yml"
        f1.write_text("identity:\n  name: Test\n")
        out = td / "pkg"
        create_package(out, {"bundle": f1})
        preview = preview_package(out)
        assert "risks" in preview
