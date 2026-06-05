"""T-RDE tests for Review Decision Audit Trail (Phase 8)."""
import tempfile
from pathlib import Path

from sayane.core.audit_trail import AuditStore, build_audit_record, get_audit_store
from sayane.core.review_decision import OverlapResolution, ReviewDecision


def _make_reject_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-reject",
        decision="reject",
        reason="RDE and Sayane should not be flattened into generic technical preferences.",
        original_section="technical",
        original_action="add",
        original_proposed={"preferences": ["RDE", "Sayane"]},
        review_flags=["review_required", "unstable_placement", "semantic_overlap"],
        review_warnings=[{"type": "unstable_placement", "term": "RDE", "message": "RDE may be flattened."}],
        transfer_path=["Sayane", "ChatGPT", "Claude", "Sayane"],
    )


def _make_modify_decision() -> ReviewDecision:
    return ReviewDecision(
        candidate_id="c-modify",
        decision="modify",
        reason="RDE belongs to principles; Sayane represented as context portability basis.",
        applied_value={"principles": ["RDE", "Context portability via Sayane"]},
        original_section="principles",
        original_action="add",
        original_proposed={"principles": ["RDE", "Sayane"]},
        review_flags=["semantic_overlap", "review_required"],
        transfer_path=["Sayane", "ChatGPT", "Claude", "Sayane"],
    )


def test_review_decision_creates_audit_record():
    decision = _make_reject_decision()
    record = build_audit_record(decision, profile_updated=False)
    assert record["event_type"] == "review_decision"
    assert record["decision"]["type"] == "reject"


def test_reject_audit_preserves_candidate():
    decision = _make_reject_decision()
    record = build_audit_record(decision, profile_updated=False)
    assert record["result"]["profile_updated"] is False
    assert record["candidate"]["proposed"] == {"preferences": ["RDE", "Sayane"]}
    assert record["decision"]["reason"]


def test_modify_audit_preserves_original_and_applied():
    decision = _make_modify_decision()
    record = build_audit_record(decision, profile_updated=True)
    assert record["result"]["profile_updated"] is True
    assert record["diff"]["original_candidate"] == {"principles": ["RDE", "Sayane"]}
    assert record["diff"]["applied_value"] == {"principles": ["RDE", "Context portability via Sayane"]}
    assert "Modified:" in record["diff"]["delta_summary"]


def test_audit_record_preserves_semantic_warnings():
    decision = _make_reject_decision()
    record = build_audit_record(decision)
    assert record["candidate"]["flags"] == ["review_required", "unstable_placement", "semantic_overlap"]
    assert len(record["candidate"]["warnings"]) >= 1


def test_audit_store_append_only():
    with tempfile.TemporaryDirectory() as d:
        store = AuditStore(Path(d))
        decision = _make_reject_decision()
        record = build_audit_record(decision)
        store.append(record)

        # Read back
        records = store.read_all()
        assert len(records) == 1
        assert records[0]["id"] == record["id"]

        # Append another — first record unchanged
        d2 = _make_modify_decision()
        r2 = build_audit_record(d2, profile_updated=True)
        store.append(r2)
        records = store.read_all()
        assert len(records) == 2
        assert records[0]["id"] == record["id"]  # first unchanged


def test_audit_query_by_candidate():
    with tempfile.TemporaryDirectory() as d:
        store = AuditStore(Path(d))
        store.append(build_audit_record(_make_reject_decision()))
        store.append(build_audit_record(_make_modify_decision(), profile_updated=True))
        matches = store.query(candidate_id="c-reject")
        assert len(matches) == 1
        assert matches[0]["decision"]["type"] == "reject"


def test_audit_query_by_term():
    with tempfile.TemporaryDirectory() as d:
        store = AuditStore(Path(d))
        store.append(build_audit_record(_make_reject_decision()))
        store.append(build_audit_record(_make_modify_decision(), profile_updated=True))
        matches = store.query(term="RDE")
        assert len(matches) >= 1


def test_audit_query_by_decision_type():
    with tempfile.TemporaryDirectory() as d:
        store = AuditStore(Path(d))
        store.append(build_audit_record(_make_reject_decision()))
        store.append(build_audit_record(_make_modify_decision(), profile_updated=True))
        matches = store.query(decision_type="modify")
        assert len(matches) == 1
        assert matches[0]["candidate"]["id"] == "c-modify"


def test_empty_store_returns_empty_list():
    with tempfile.TemporaryDirectory() as d:
        store = AuditStore(Path(d))
        assert store.read_all() == []


def test_audit_record_includes_transfer_path():
    decision = _make_reject_decision()
    record = build_audit_record(decision)
    assert record["source"]["transfer_path"] == ["Sayane", "ChatGPT", "Claude", "Sayane"]
