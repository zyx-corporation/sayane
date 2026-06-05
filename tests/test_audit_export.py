"""T-RDE tests for Audit Trail Export (Phase 14)."""
import json
import tempfile
from pathlib import Path

from sayane.core.audit_trail import AuditStore, build_audit_record
from sayane.core.audit_export import build_export, _filter_records
from sayane.core.review_decision import ReviewDecision


def _store_with_two_records() -> tuple[AuditStore, Path]:
    d = tempfile.mkdtemp()
    store = AuditStore(Path(d))
    reject = ReviewDecision(
        candidate_id="c-reject",
        decision="reject",
        reason="Bad section.",
        original_section="technical",
        original_proposed={"preferences": ["RDE", "Sayane"]},
        review_flags=["review_required"],
        transfer_path=["Sayane", "ChatGPT"],
    )
    modify = ReviewDecision(
        candidate_id="c-modify",
        decision="modify",
        reason="Normalized.",
        applied_value={"principles": ["RDE", "Context portability via Sayane"]},
        original_section="principles",
        original_proposed={"principles": ["RDE", "Sayane"]},
        review_flags=["semantic_overlap"],
        transfer_path=["Sayane", "ChatGPT", "Claude"],
    )
    store.append(build_audit_record(reject))
    store.append(build_audit_record(modify, profile_updated=True))
    return store, Path(d)


def test_audit_export_markdown_includes_summary_and_records():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown")
    assert "# Sayane Audit Trail Export" in md
    assert "## Summary" in md
    assert "## Records" in md


def test_audit_export_includes_rejected_candidate():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown")
    assert "REJECT" in md
    assert "<none>" in md  # applied value for reject


def test_audit_export_includes_modify_diff():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown")
    assert "MODIFY" in md
    assert "RDE" in md


def test_audit_export_json_valid_schema():
    store, _ = _store_with_two_records()
    js = build_export(store, format="json")
    data = json.loads(js)
    assert data["schema_version"] == "audit-export-v1"
    assert "records" in data
    assert len(data["records"]) == 2


def test_audit_export_jsonl_valid_lines():
    store, _ = _store_with_two_records()
    jl = build_export(store, format="jsonl")
    lines = jl.strip().split("\n")
    assert len(lines) == 2
    for line in lines:
        json.loads(line)  # must parse


def test_audit_export_filter_by_decision():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown", decision="reject")
    assert "REJECT" in md
    assert "MODIFY" not in md


def test_audit_export_filter_by_term():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown", term="Sayane")
    assert "RDE" in md  # RDE appears alongside Sayane in original


def test_audit_export_redaction_keeps_decision_context():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown", redact=True)
    assert "REJECT" in md  # decision context preserved
    assert "MODIFY" in md


def test_audit_export_empty_result_not_error():
    store, _ = _store_with_two_records()
    md = build_export(store, format="markdown", term="NO_SUCH_TERM_XYZ")
    assert "No audit records matched" in md


def test_export_summary_counts_correct():
    store, _ = _store_with_two_records()
    js = build_export(store, format="json")
    data = json.loads(js)
    assert data["summary"]["decisions"]["reject"] == 1
    assert data["summary"]["decisions"]["modify"] == 1
