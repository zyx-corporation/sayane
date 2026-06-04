"""Unit tests for lineage query builder."""

from sayane.bridge.capture_store import save_capture
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CaptureRequest
from sayane.lineage.query import build_candidate_lineage


def test_merge_caps_suspicious_for_list_add(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("SAYANE_HOME", str(tmp_path))
    cfg = BridgeConfig()
    captured = save_capture(
        cfg,
        CaptureRequest(
            content='important_terms:\n  - "X"\n  - "Y"\n',
            source="clipboard",
            capture_source="clipboard",
            profile_id="default",
            section="important_terms",
        ),
    )
    lineage = build_candidate_lineage(cfg, captured.id)
    assert lineage.capture_id == captured.id
    assert lineage.source_kind == "clipboard"
    assert lineage.section == "important_terms"
    assert any(e.operation == "capture_created" for e in lineage.events)


def test_lineage_reads_legacy_approve_record(tmp_path, monkeypatch) -> None:
    from sayane.storage.lineage_store import append_record

    monkeypatch.setenv("SAYANE_HOME", str(tmp_path))
    cfg = BridgeConfig()
    captured = save_capture(
        cfg,
        CaptureRequest(
            content='important_terms:\n  - "Z"\n',
            source="clipboard",
            capture_source="clipboard",
            profile_id="default",
            section="important_terms",
        ),
    )
    append_record(
        cfg,
        "default",
        "candidate_approved",
        {"candidate_id": captured.id, "section": "important_terms"},
    )
    lineage = build_candidate_lineage(cfg, captured.id)
    assert any(e.operation == "candidate_approved" for e in lineage.events)
