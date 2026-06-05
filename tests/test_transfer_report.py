"""T-RDE tests for Transfer Regression Dashboard (Phase 10)."""
import tempfile
from pathlib import Path

from sayane.core.audit_trail import AuditStore
from sayane.core.transfer_report import generate_transfer_report, render_markdown_report


def test_transfer_report_generates_markdown():
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        md = render_markdown_report(report)
        assert "# Sayane Cross-LLM Transfer Regression Report" in md
        assert "## Summary" in md
        assert "## Regression Status" in md


def test_transfer_report_status_with_no_fixtures():
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        assert report["status"] == "PASS"
        assert report["summary"]["fixtures"] == 0


def test_transfer_report_json_structure():
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        assert "generated_at" in report
        assert "status" in report
        assert "summary" in report
        assert "phases" in report
        assert "bundles" in report
        assert "candidates" in report
        assert "audit" in report
        assert "regressions" in report


def test_transfer_report_includes_phase_status():
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        md = render_markdown_report(report)
        # Phase section exists even if no phase records
        assert "## Regression Status" in md


def test_hash_mismatch_flagged_as_critical():
    """When a bundle has hash mismatch, it should be a critical regression."""
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        # Create a fixture with a mismatched hash
        import yaml
        fixture = transfer_dir / "bad-hash.yml"
        fixture.write_text("identity:\n  name: Test\ncontent_hash:\n  value: '0000000000000000000000000000000000000000000000000000000000000000'\n")
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        assert report["status"] == "FAIL"
        assert report["summary"]["critical_regressions"] >= 1


def test_unverified_bundle_flagged_as_warning():
    with tempfile.TemporaryDirectory() as d:
        transfer_dir = Path(d)
        fixture = transfer_dir / "no-hash.yml"
        fixture.write_text("identity:\n  name: Test\n")
        audit_store = AuditStore(Path(d))
        profile_path = Path("examples/profiles/minimal.yaml")

        report = generate_transfer_report(transfer_dir, audit_store, profile_path)
        assert report["status"] == "PASS_WITH_WARNINGS"
        assert report["summary"]["warnings"] >= 1
