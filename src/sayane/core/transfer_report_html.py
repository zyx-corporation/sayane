"""Transfer Regression HTML Dashboard (F-5).

Static HTML dashboard for observing transfer regression status,
scoped context risks, MCP boundary checks, and package preview risks.
Observation surface only — not enforcement.
"""

from __future__ import annotations

from typing import Any


def render_html_report(report: dict[str, Any]) -> str:
    """Render transfer regression report as a static HTML dashboard."""
    s = report.get("summary", {})
    status = report.get("status", "?")
    status_colors = {"PASS": "#22c55e", "PASS_WITH_WARNINGS": "#eab308", "FAIL": "#dc2626"}

    def _card(label: str, value: Any, color: str = "") -> str:
        c = f' style="color:{color}"' if color else ""
        return f'<div class="card"><span class="label">{label}</span><span class="value"{c}>{value}</span></div>'

    critical = s.get("critical_regressions", 0)
    warnings_val = s.get("warnings", 0)

    html = f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sayane Transfer Regression Dashboard</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 960px; margin: 0 auto; padding: 24px; background: #f8fafc; color: #1e293b; }}
h1 {{ font-size: 1.5rem; margin-bottom: 4px; }}
h2 {{ font-size: 1.2rem; margin: 24px 0 12px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px; }}
.cards {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(170px, 1fr)); gap: 12px; margin: 16px 0; }}
.card {{ background: white; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
.card .label {{ display: block; font-size: .75rem; color: #64748b; text-transform: uppercase; }}
.card .value {{ display: block; font-size: 1.5rem; font-weight: 700; margin-top: 4px; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,.1); }}
th, td {{ text-align: left; padding: 10px 14px; border-bottom: 1px solid #e2e8f0; }}
th {{ background: #f1f5f9; font-weight: 600; font-size: .85rem; }}
td {{ font-size: .9rem; }}
tr:last-child td {{ border-bottom: none; }}
.risk-critical {{ color: #dc2626; font-weight: 600; }}
.risk-warning {{ color: #b45309; }}
.boundary {{ background: #fef3c7; border-left: 4px solid #eab308; padding: 12px 16px; border-radius: 4px; font-size: .85rem; margin: 16px 0; }}
.boundary strong {{ color: #92400e; }}
.footer {{ font-size: .75rem; color: #94a3b8; margin-top: 32px; text-align: center; }}
</style>
</head>
<body>
<h1>Sayane Transfer Regression Dashboard</h1>
<p>Generated: {report.get('generated_at', '?')}</p>

<div class="cards">
{_card("Overall", status, status_colors.get(status, "#64748b"))}
{_card("Critical", critical, "#dc2626" if critical else "")}
{_card("Warnings", warnings_val, "#b45309" if warnings_val else "")}
{_card("Verified", s.get("verified_bundles", "?"))}
{_card("Unverified", s.get("unverified_bundles", "?"))}
{_card("Scoped Accept", s.get("scoped_accept_count", "0"))}
{_card("Promotion Risk", s.get("promotion_risk_count", "0"))}
</div>

<h2>Phase Status</h2>
<table>
<tr><th>Phase</th><th>Status</th><th>Tests</th></tr>
"""
    phases = report.get("phases", [])
    for p in phases:
        html += f"<tr><td>{p.get('phase','?')}</td><td>{p.get('status','?')}</td><td>{p.get('tests','?')}</td></tr>\n"
    html += "</table>\n"

    # Scoped context
    html += """
<h2>Scoped Context</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
"""
    scoped = report.get("scoped_context", {})
    for label, key in [
        ("scoped_accept entries", "scoped_accept_count"),
        ("missing accepted_scope", "accepted_scope_missing"),
        ("missing conditions", "conditions_missing"),
        ("missing negative_constraints", "negative_constraints_missing"),
        ("promotion risk", "promotion_risk_count"),
    ]:
        v = scoped.get(key, "not recorded")
        cls = ' class="risk-warning"' if isinstance(v, int) and v > 0 else ""
        html += f'<tr><td>{label}</td><td{cls}>{v}</td></tr>\n'
    html += "</table>\n"

    # MCP Boundary
    html += """
<h2>MCP Boundary</h2>
<table>
<tr><th>Check</th><th>Status</th></tr>
"""
    mcp = report.get("mcp_boundary", {})
    for label, key in [
        ("Derived context", "is_derived_context"),
        ("Canonical profile", "is_canonical_profile"),
        ("Scope preserved", "scope_preserved"),
        ("Conditions preserved", "conditions_preserved"),
        ("Negative constraints preserved", "negative_constraints_preserved"),
    ]:
        v = mcp.get(key, "not recorded")
        cls = ""
        html += f'<tr><td>{label}</td><td{cls}>{v}</td></tr>\n'
    html += "</table>\n"

    # Audit decisions
    html += """
<h2>Audit Decisions</h2>
<table>
<tr><th>Type</th><th>Count</th></tr>
"""
    audit = report.get("audit_summary", {})
    for dtype in ["approve", "reject", "modify", "defer", "scoped_accept"]:
        v = audit.get(dtype, "0")
        html += f"<tr><td>{dtype}</td><td>{v}</td></tr>\n"
    html += "</table>\n"

    # Package preview
    pp = report.get("package_preview", {})
    html += f"""
<h2>Package Preview</h2>
<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Previews</td><td>{pp.get('preview_count', '0')}</td></tr>
<tr><td>Profile modified</td><td>{pp.get('profile_modified', 'false')}</td></tr>
<tr><td>Preview only</td><td>{pp.get('preview_only', 'true')}</td></tr>
</table>
"""

    # Boundary footer
    html += f"""
<div class="boundary">
<strong>Observation surface, not enforcement.</strong><br>
Dashboard does not auto-fix candidates, auto-accept packages, or auto-promote scoped context.<br>
Verified packages are not automatically accepted. Scoped context is not global context.
</div>

<p class="footer">Sayane Transfer Regression Dashboard — generated {report.get('generated_at', '?')}</p>
</body>
</html>
"""
    return html
