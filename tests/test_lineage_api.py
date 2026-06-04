"""Bridge lineage API (#125)."""

from __future__ import annotations

import json

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sayane.bridge.app import create_app
from sayane.bridge.auth import load_or_create_token
from sayane.bridge.capture_store import save_capture
from sayane.bridge.config import BridgeConfig
from sayane.bridge.models import CaptureRequest
from sayane.evaluators.service import evaluate_candidate
from sayane.storage.candidates import load_candidate


@pytest.fixture
def bridge_env(tmp_path: Path) -> tuple[TestClient, BridgeConfig, str]:
    home = tmp_path / "sayane"
    config = BridgeConfig(home=home)
    token, _ = load_or_create_token(config)
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    client = TestClient(create_app(config))
    return client, config, token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_candidate_lineage_after_capture_and_evaluate(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, cfg, token = bridge_env
    headers = _auth(token)

    captured = save_capture(
        cfg,
        CaptureRequest(
            content='important_terms:\n  - "Alpha"\n  - "Beta"\n',
            source="clipboard",
            capture_source="clipboard",
            profile_id="default",
            section="important_terms",
        ),
    )
    cid = captured.id

    res = client.get(f"/candidates/{cid}/lineage", headers=headers)
    assert res.status_code == 200
    body = res.json()
    assert body["capture_id"] == cid
    assert body["candidate_id"] == cid
    assert body["source_kind"] == "clipboard"
    assert body["decision"] == "pending"
    ops = {e["operation"] for e in body["events"]}
    assert "capture_created" in ops
    assert "candidate_generated" in ops

    client.post(
        f"/candidates/{cid}/evaluate",
        headers=headers,
        json={"level": 1},
    )
    res2 = client.get(f"/candidates/{cid}/lineage", headers=headers)
    assert res2.status_code == 200
    body2 = res2.json()
    assert body2["decision"] in ("evaluated", "pending")
    assert body2.get("rde_class")
    assert "candidate_evaluated" in {e["operation"] for e in body2["events"]}


def test_capture_lineage_alias(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, cfg, token = bridge_env
    headers = _auth(token)
    captured = save_capture(
        cfg,
        CaptureRequest(
            content='important_terms:\n  - "One"\n',
            source="selection",
            capture_source="selection",
            profile_id="default",
            section="important_terms",
        ),
    )
    res = client.get(f"/captures/{captured.id}/lineage", headers=headers)
    assert res.status_code == 200
    assert res.json()["capture_id"] == captured.id


def test_lineage_jsonl_on_approve(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, cfg, token = bridge_env
    headers = _auth(token)
    captured = save_capture(
        cfg,
        CaptureRequest(
            content='important_terms:\n  - "MergeMe"\n',
            source="clipboard",
            capture_source="clipboard",
            profile_id="default",
            section="important_terms",
        ),
    )
    cid = captured.id
    evaluate_candidate(cfg, cid, level=1)
    candidate = load_candidate(cfg, cid)
    assert candidate.evaluation

    client.post(
        f"/candidates/{cid}/approve",
        headers=headers,
        json={
            "force_critical": False,
            "explicit_confirmation": {
                "section": "important_terms",
                "checked": True,
                "reason": "確認済み",
                "confirmed_at": "2026-06-04T12:00:00Z",
            },
        },
    )

    path = cfg.home / "lineage" / "default.jsonl"
    assert path.exists()
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    approved = [ln for ln in lines if ln.get("event") == "candidate_approved"]
    assert approved
    assert approved[-1]["candidate_id"] == cid
    assert approved[-1].get("context_path") == "important_terms" or approved[-1].get(
        "section"
    ) == "important_terms"
