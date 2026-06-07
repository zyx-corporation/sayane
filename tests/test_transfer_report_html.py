"""T-RDE tests for Transfer Regression HTML Dashboard (F-5)."""
from sayane.core.transfer_report_html import render_html_report


def test_html_dashboard_generates_valid_html():
    report = {
        "generated_at": "2026-06-07T00:00:00Z",
        "status": "PASS_WITH_WARNINGS",
        "summary": {
            "critical_regressions": 0,
            "warnings": 2,
            "verified_bundles": 3,
            "unverified_bundles": 1,
            "scoped_accept_count": 1,
            "promotion_risk_count": 1,
        },
        "phases": [
            {"phase": "F-1.5 Scoped Context Acceptance", "status": "Completed", "tests": 7},
            {"phase": "F-2 MCP Scoped Context Output", "status": "Completed", "tests": 7},
        ],
        "scoped_context": {
            "scoped_accept_count": 1,
            "accepted_scope_missing": 0,
            "conditions_missing": 0,
            "negative_constraints_missing": 0,
            "promotion_risk_count": 1,
        },
        "mcp_boundary": {
            "is_derived_context": True,
            "is_canonical_profile": False,
            "scope_preserved": True,
            "conditions_preserved": True,
            "negative_constraints_preserved": True,
        },
        "audit_summary": {"approve": 2, "reject": 1, "modify": 1, "defer": 0, "scoped_accept": 1},
        "package_preview": {"preview_count": 2, "profile_modified": "false", "preview_only": "true"},
    }
    html = render_html_report(report)
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "Sayane Transfer Regression Dashboard" in html


def test_html_dashboard_shows_summary_cards():
    report = {"generated_at": "x", "status": "PASS", "summary": {"critical_regressions": 0, "warnings": 0, "verified_bundles": "?", "unverified_bundles": "?", "scoped_accept_count": "2", "promotion_risk_count": "1"}, "phases": [], "scoped_context": {}, "mcp_boundary": {}, "audit_summary": {}, "package_preview": {}}
    html = render_html_report(report)
    assert "Scoped Accept" in html
    assert "Promotion Risk" in html


def test_html_dashboard_shows_scoped_accept_section():
    report = {"generated_at": "x", "status": "PASS", "summary": {"scoped_accept_count": "2"}, "phases": [], "scoped_context": {"scoped_accept_count": 2, "accepted_scope_missing": 0}, "mcp_boundary": {}, "audit_summary": {}, "package_preview": {}}
    html = render_html_report(report)
    assert "scoped_accept entries" in html


def test_html_dashboard_shows_mcp_boundary():
    report = {"generated_at": "x", "status": "PASS", "summary": {}, "phases": [], "scoped_context": {}, "mcp_boundary": {"is_derived_context": True, "is_canonical_profile": False}, "audit_summary": {}, "package_preview": {}}
    html = render_html_report(report)
    assert "Derived context" in html
    assert "Canonical profile" in html


def test_html_dashboard_shows_scoped_accept_separate_from_approve():
    report = {"generated_at": "x", "status": "PASS", "summary": {}, "phases": [], "scoped_context": {}, "mcp_boundary": {}, "audit_summary": {"approve": 3, "scoped_accept": 1}, "package_preview": {}}
    html = render_html_report(report)
    assert "scoped_accept" in html


def test_html_dashboard_boundary_visible():
    report = {"generated_at": "x", "status": "PASS", "summary": {}, "phases": [], "scoped_context": {}, "mcp_boundary": {}, "audit_summary": {}, "package_preview": {}}
    html = render_html_report(report)
    assert "Observation surface" in html
    assert "not automatically accepted" in html


def test_html_dashboard_no_external_js():
    report = {"generated_at": "x", "status": "PASS", "summary": {}, "phases": [], "scoped_context": {}, "mcp_boundary": {}, "audit_summary": {}, "package_preview": {}}
    html = render_html_report(report)
    assert "<script src=" not in html
