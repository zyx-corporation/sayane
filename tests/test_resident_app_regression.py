"""GUI-level resident app regression paths over the Bridge-hosted local shell."""

from __future__ import annotations

import shutil
from pathlib import Path

from fastapi.testclient import TestClient

from sayane.bridge.app import create_app
from sayane.bridge.auth import load_or_create_token
from sayane.bridge.config import BridgeConfig


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _bridge_env(tmp_path: Path) -> tuple[TestClient, BridgeConfig, str]:
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


def test_resident_app_gui_operator_path_capture_review_revise_approve(
    tmp_path: Path,
) -> None:
    client, config, token = _bridge_env(tmp_path)

    bootstrap = client.get("/app/ui?locale=ja", headers=_auth(token))
    assert bootstrap.status_code == 200
    assert "紗綾音 Resident App ホーム" in bootstrap.text

    capture = client.post(
        "/app/ui/capture-clipboard",
        data={"content": "Resident app regression candidate", "locale": "ja"},
        follow_redirects=False,
    )
    assert capture.status_code == 303
    detail_path = capture.headers["location"]
    detail_base_path = detail_path.split("?", 1)[0]

    detail = client.get(detail_path)
    assert detail.status_code == 200
    assert "Resident app regression candidate" in detail.text
    assert "候補詳細" in detail.text

    diff = client.get(detail_base_path + "/diff")
    assert diff.status_code == 200
    assert "候補差分" in diff.text

    evaluated = client.post(
        detail_base_path + "/evaluate",
        data={"level": "1"},
        follow_redirects=False,
    )
    assert evaluated.status_code == 303
    evaluated_page = client.get(evaluated.headers["location"])
    assert evaluated_page.status_code == 200
    assert "候補を評価しました。" in evaluated_page.text

    revised = client.post(
        detail_base_path + "/revise",
        data={
            "edited_text": "Resident app regression revised candidate",
            "target_section": "knowledge.concepts",
            "change_reason": "operator wording cleanup",
        },
        follow_redirects=False,
    )
    assert revised.status_code == 303
    revised_path = revised.headers["location"]
    revised_base_path = revised_path.split("?", 1)[0]

    revised_page = client.get(revised_path)
    assert revised_page.status_code == 200
    assert "修正版候補を作成しました。" in revised_page.text
    assert "Resident app regression revised candidate" in revised_page.text

    re_evaluated = client.post(
        revised_base_path + "/evaluate",
        data={"level": "1"},
        follow_redirects=False,
    )
    assert re_evaluated.status_code == 303

    approved = client.post(
        revised_base_path + "/approve",
        data={},
        follow_redirects=False,
    )
    assert approved.status_code == 303
    approved_queue = client.get(approved.headers["location"])
    assert approved_queue.status_code == 200
    assert "候補を承認しました。" in approved_queue.text
    assert "候補キュー" in approved_queue.text

    from sayane.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("Resident app regression revised candidate" in concept for concept in concepts)


def test_resident_app_gui_operator_path_rejects_candidate(
    tmp_path: Path,
) -> None:
    client, _, token = _bridge_env(tmp_path)

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/ui/capture-clipboard",
        data={"content": "Resident app regression reject candidate"},
        follow_redirects=False,
    )
    assert capture.status_code == 303
    detail_base_path = capture.headers["location"].split("?", 1)[0]

    rejected = client.post(
        detail_base_path + "/reject",
        data={"reason": "no longer needed"},
        follow_redirects=False,
    )
    assert rejected.status_code == 303

    queue = client.get(rejected.headers["location"])
    assert queue.status_code == 200
    assert "Candidate rejected." in queue.text or "候補を却下しました。" in queue.text


def test_resident_app_gui_operator_path_daemon_panel(
    tmp_path: Path,
) -> None:
    client, _, token = _bridge_env(tmp_path)

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    daemon = client.get("/app/ui/daemon")
    assert daemon.status_code == 200
    assert "紗綾音 Resident App Daemon Panel" in daemon.text
    assert "Runtime Init Preview" in daemon.text
    assert "Cleanup Preview" in daemon.text
    assert "Repair Preview" in daemon.text

    daemon_state = client.get("/app/ui-state/daemon")
    assert daemon_state.status_code == 200
    payload = daemon_state.json()
    assert payload["kind"] == "resident_app_daemon_panel_screen_state"
    assert payload["summary_cards"][0]["key"] == "state"


def test_resident_app_gui_shell_json_state_and_logout_path(
    tmp_path: Path,
) -> None:
    client, _, token = _bridge_env(tmp_path)

    bootstrap = client.get("/app/ui?locale=ja", headers=_auth(token))
    assert bootstrap.status_code == 200
    assert "紗綾音 Resident App ホーム" in bootstrap.text

    home_state = client.get("/app/ui-state/home")
    assert home_state.status_code == 200
    assert home_state.json()["kind"] == "resident_app_home_screen_state"

    captured = client.post(
        "/app/ui-action/capture-clipboard",
        json={
            "content": "Resident app JSON shell candidate",
            "locale": "ja",
            "profile_id": "default",
        },
    )
    assert captured.status_code == 200
    candidate_id = captured.json()["id"]

    queue_state = client.get("/app/ui-state/candidates")
    assert queue_state.status_code == 200
    queue_payload = queue_state.json()
    assert queue_payload["kind"] == "resident_app_candidate_queue_screen_state"
    assert any(item["id"] == candidate_id for item in queue_payload["items"])

    detail_state = client.get(f"/app/ui-state/candidates/{candidate_id}")
    assert detail_state.status_code == 200
    assert detail_state.json()["kind"] == "resident_app_candidate_detail_screen_state"

    diff_state = client.get(f"/app/ui-state/candidates/{candidate_id}/diff")
    assert diff_state.status_code == 200
    diff_payload = diff_state.json()
    assert diff_payload["candidate_id"] == candidate_id
    assert "ui_summary" in diff_payload

    lineage_state = client.get(f"/app/ui-state/candidates/{candidate_id}/lineage")
    assert lineage_state.status_code == 200
    assert lineage_state.json()["candidate_id"] == candidate_id

    evaluated = client.post(
        f"/app/ui-action/candidates/{candidate_id}/evaluate",
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "evaluated"

    revised = client.post(
        f"/app/ui-action/candidates/{candidate_id}/revise",
        json={
            "edited_text": "Resident app JSON shell revised candidate",
            "target_section": "knowledge.concepts",
            "change_reason": "json shell regression path",
        },
    )
    assert revised.status_code == 200
    revised_id = revised.json()["id"]

    re_evaluated = client.post(
        f"/app/ui-action/candidates/{revised_id}/evaluate",
        json={"level": 1},
    )
    assert re_evaluated.status_code == 200
    assert re_evaluated.json()["status"] == "evaluated"

    approved = client.post(
        f"/app/ui-action/candidates/{revised_id}/approve",
        json={"force_critical": False, "override_reason": None},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    daemon_state = client.get("/app/ui-state/daemon")
    assert daemon_state.status_code == 200
    assert daemon_state.json()["kind"] == "resident_app_daemon_panel_screen_state"

    logout = client.post("/app/ui-action/session/logout")
    assert logout.status_code == 200
    assert logout.json()["status"] == "logged_out"

    home_after_logout = client.get("/app/ui-state/home")
    assert home_after_logout.status_code == 401
    assert home_after_logout.json()["detail"] == "Missing or invalid resident app UI session"

    queue_after_logout = client.get("/app/ui/candidates")
    assert queue_after_logout.status_code == 401
    assert queue_after_logout.json()["detail"] == "Missing or invalid resident app UI session"

    capture_after_logout = client.post(
        "/app/ui-action/capture-clipboard",
        json={"content": "blocked after logout"},
    )
    assert capture_after_logout.status_code == 401
    assert capture_after_logout.json()["detail"] == "Missing or invalid resident app UI session"
