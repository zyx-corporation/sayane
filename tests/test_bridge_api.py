import json
import shutil
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

from sayane.bridge.app import create_app
from sayane.bridge.auth import load_or_create_token
from sayane.bridge.config import BridgeConfig
from sayane.evaluators.judge_config import JudgeConfig
from sayane.evaluators.llm_judge import LLMJudgeRequestError


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


def test_health_without_auth(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, _ = bridge_env
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "source_updated_at" in data
    assert data.get("component") == "sayane"


def test_profiles_requires_auth(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, _ = bridge_env
    assert client.get("/profiles").status_code == 401


def test_profiles_lists_default(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, token = bridge_env
    response = client.get("/profiles", headers=_auth(token))
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "default"
    assert data[0]["name"] == "Example User"
    assert data[0]["default_language"] == "ja"


def test_app_daemon_overview_requires_auth(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env
    assert client.get("/app/daemon-overview").status_code == 401


def test_app_daemon_overview_returns_preview_payload(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    response = client.get("/app/daemon-overview", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_daemon_overview_preview"
    assert payload["runtime_root"] == str(config.home / "run")
    assert payload["status"]["kind"] == "resident_daemon_lifecycle_status"
    assert payload["liveness"]["kind"] == "resident_daemon_liveness_diagnostic_preview"
    assert payload["readiness"]["kind"] == "resident_daemon_readiness_diagnostic_preview"
    assert payload["service_targets_status"]["kind"] == "resident_daemon_service_targets_status"
    assert any(
        item["command"] == "sayane app daemon-operator-phase-status --json"
        for item in payload["next_actions"]
    )
    if sys.platform == "darwin":
        assert payload["launchagent_preview"]["kind"] == "resident_daemon_launchagent_plan"
        assert payload["launchagent_status"]["kind"] == "resident_daemon_launchagent_status"
    else:
        assert payload["launchagent_preview"] is None
        assert payload["launchagent_status"] is None
    assert payload["is_preview"] is True


def test_app_overview_requires_auth(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env
    assert client.get("/app/overview").status_code == 401
    assert client.get("/app/operator-phase-status").status_code == 401
    assert client.get("/app/screen-state/home").status_code == 401


def test_app_ui_requires_auth(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env
    assert client.get("/app/ui").status_code == 401
    assert client.get("/app/ui/candidates").status_code == 401
    assert client.get("/app/ui/daemon").status_code == 401
    assert client.get("/app/ui-state/home").status_code == 401
    assert client.get("/app/ui-state/operator-phase-status").status_code == 401
    assert client.post("/app/ui-action/capture-clipboard", json={"content": "hello"}).status_code == 401


def test_app_ui_state_auth_failure_returns_explicit_session_error(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env

    home = client.get("/app/ui-state/home")
    assert home.status_code == 401
    assert home.json()["detail"] == "Missing or invalid resident app UI session"

    capture = client.post("/app/ui-action/capture-clipboard", json={"content": "hello"})
    assert capture.status_code == 401
    assert capture.json()["detail"] == "Missing or invalid resident app UI session"


def test_app_contract_requires_auth(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env
    assert client.get("/app/contract").status_code == 401


def test_app_contract_returns_handoff_metadata(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.get("/app/contract", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_app_contract"
    assert payload["contract_version"] == "1"
    assert payload["preferred_entrypoint"] == "/app/overview"


def test_app_overview_returns_aggregate_payload(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.get("/app/overview", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_app_overview"
    assert payload["runtime"]["profile_id"] == "default"
    assert payload["summary"]["repository_available"] is False
    assert payload["review_queue"]["kind"] == "resident_review_queue"
    assert payload["mcp_preview"]["preview"]["kind"] == "resident_mcp_preview"
    assert payload["daemon_overview"]["kind"] == "resident_daemon_overview_preview"


def test_app_operator_phase_status_returns_aggregate_payload(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    response = client.get("/app/operator-phase-status", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_daemon_operator_phase_status"
    assert payload["runtime_root"] == str(config.home / "run")
    assert payload["phase_readiness"] == "not_ready_for_phase_closure"


def test_app_home_screen_state_returns_framework_neutral_state(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.get("/app/screen-state/home", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_app_home_screen_state"
    assert payload["quick_links"][0]["screen"] == "candidate_queue"


def test_app_ui_operator_phase_state_returns_cookie_backed_payload(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    response = client.get("/app/ui-state/operator-phase-status")
    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_daemon_operator_phase_status"
    assert payload["phase_readiness"] == "not_ready_for_phase_closure"


def test_app_ui_returns_bootstrap_home_html(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.get("/app/ui", headers=_auth(token))

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    text = response.text
    assert "紗綾音 Resident App Home" in text
    assert "/app/overview" in text
    assert "Presentation-only" in text
    assert "review required" in text or "No reviewable candidates." in text
    assert "/app/ui-state/home" in text
    assert "/app/ui-action/capture-clipboard" in text
    assert "sayane_bridge_ui_session" in response.cookies


def test_app_ui_follow_up_routes_require_dedicated_ui_session_not_raw_bearer(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    queue = client.get("/app/ui/candidates", headers=_auth(token))
    assert queue.status_code == 401
    assert queue.json()["detail"] == "Missing or invalid resident app UI session"

    state = client.get("/app/ui-state/home", headers=_auth(token))
    assert state.status_code == 401
    assert state.json()["detail"] == "Missing or invalid resident app UI session"

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    queue_with_session = client.get("/app/ui/candidates")
    assert queue_with_session.status_code == 200

    state_with_session = client.get("/app/ui-state/home")
    assert state_with_session.status_code == 200


def test_app_ui_persists_japanese_locale_across_cookie_navigation(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    home = client.get("/app/ui?locale=ja", headers=_auth(token))
    assert home.status_code == 200
    assert 'lang="ja"' in home.text
    assert "<title>紗綾音 Resident App ホーム</title>" in home.text
    assert "ホーム" in home.text
    assert home.cookies.get("sayane_bridge_ui_locale") == "ja"

    queue = client.get("/app/ui/candidates")
    assert queue.status_code == 200
    assert "<title>紗綾音 Resident App 候補キュー</title>" in queue.text
    assert "Resident App 候補キュー" in queue.text
    assert "保留" in queue.text or "評価済み" in queue.text or "レビュー可能な候補はありません。" in queue.text
    assert "未評価" in queue.text or "レビュー可能な候補はありません。" in queue.text
    assert "pending" in queue.text or "evaluated" in queue.text or "停止中" in home.text


def test_app_ui_candidate_queue_detail_and_diff_html(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "Resident app HTML review flow"},
    )
    assert capture.status_code == 200
    candidate_id = capture.json()["id"]

    queue = client.get("/app/ui/candidates")
    assert queue.status_code == 200
    assert "text/html" in queue.headers["content-type"]
    assert f"/app/ui/candidates/{candidate_id}" in queue.text
    assert "Queue Status Counts" in queue.text
    assert "Top Sections" in queue.text

    detail = client.get(f"/app/ui/candidates/{candidate_id}")
    assert detail.status_code == 200
    assert "Candidate Detail" in detail.text
    assert "Resident app HTML review flow" in detail.text
    assert f"/app/ui/candidates/{candidate_id}/diff" in detail.text
    assert "<dt>Section</dt>" in detail.text
    assert "<dt>Operation</dt>" in detail.text

    diff = client.get(f"/app/ui/candidates/{candidate_id}/diff")
    assert diff.status_code == 200
    assert "Candidate Diff" in diff.text
    assert "Diff Summary" in diff.text
    assert "add" in diff.text


def test_app_ui_bootstrap_replaces_prior_dedicated_session(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    first = client.get("/app/ui", headers=_auth(token))
    assert first.status_code == 200
    first_session = first.cookies.get("sayane_bridge_ui_session")
    assert first_session

    second = client.get("/app/ui", headers=_auth(token))
    assert second.status_code == 200
    second_session = second.cookies.get("sayane_bridge_ui_session")
    assert second_session
    assert second_session != first_session

    stale_client = TestClient(client.app)
    stale_client.cookies.set("sayane_bridge_ui_session", first_session)
    stale = stale_client.get("/app/ui-state/home")
    assert stale.status_code == 401
    assert stale.json()["detail"] == "Missing or invalid resident app UI session"

    current = client.get("/app/ui-state/home")
    assert current.status_code == 200


def test_app_ui_session_logout_invalidates_follow_up_requests(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    logout = client.post("/app/ui-action/session/logout")
    assert logout.status_code == 200
    assert logout.json() == {"status": "logged_out"}

    follow_up = client.get("/app/ui-state/home")
    assert follow_up.status_code == 401
    assert follow_up.json()["detail"] == "Missing or invalid resident app UI session"


def test_app_ui_form_actions_work_with_ui_cookie_session(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/ui/capture-clipboard",
        data={"content": "Resident app cookie capture", "locale": "ja"},
        follow_redirects=False,
    )
    assert capture.status_code == 303
    detail_path = capture.headers["location"]
    detail_base_path = detail_path.split("?", 1)[0]
    assert detail_path.startswith("/app/ui/candidates/")
    assert "notice=" in detail_path

    detail = client.get(detail_path)
    assert detail.status_code == 200
    assert "Resident app cookie capture" in detail.text
    assert "クリップボードから保留候補を作成しました。" in detail.text

    evaluated = client.post(
        detail_base_path + "/evaluate",
        data={"level": "1"},
        follow_redirects=False,
    )
    assert evaluated.status_code == 303
    evaluated_detail = client.get(evaluated.headers["location"])
    assert evaluated_detail.status_code == 200
    assert "候補を評価しました。" in evaluated_detail.text
    assert "completed" in evaluated_detail.text or "level" in evaluated_detail.text

    revised = client.post(
        detail_base_path + "/revise",
        data={
            "edited_text": "Resident app revised cookie capture",
            "target_section": "knowledge.concepts",
            "change_reason": "clarified wording",
        },
        follow_redirects=False,
    )
    assert revised.status_code == 303
    revised_detail = client.get(revised.headers["location"])
    assert revised_detail.status_code == 200
    assert "修正版候補を作成しました。" in revised_detail.text
    assert "Resident app revised cookie capture" in revised_detail.text

    re_evaluated = client.post(
        revised.headers["location"].split("?", 1)[0] + "/evaluate",
        data={"level": "1"},
        follow_redirects=False,
    )
    assert re_evaluated.status_code == 303

    approved = client.post(
        revised.headers["location"].split("?", 1)[0] + "/approve",
        data={},
        follow_redirects=False,
    )
    assert approved.status_code == 303
    approved_queue = client.get(approved.headers["location"])
    assert approved_queue.status_code == 200
    assert "候補を承認しました。" in approved_queue.text

    from sayane.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("Resident app revised cookie capture" in concept for concept in concepts)


def test_app_ui_state_endpoints_work_with_ui_cookie_session(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    bootstrap = client.get("/app/ui?locale=ja", headers=_auth(token))
    assert bootstrap.status_code == 200

    home = client.get("/app/ui-state/home")
    assert home.status_code == 200
    assert home.json()["kind"] == "resident_app_home_screen_state"

    contract = client.get("/app/ui-state/contract")
    assert contract.status_code == 200
    assert contract.json()["kind"] == "resident_app_contract"

    capture = client.post(
        "/app/ui-action/capture-clipboard",
        json={"content": "Resident app ui state capture", "locale": "ja"},
    )
    assert capture.status_code == 200
    payload = capture.json()
    candidate_id = payload["id"]
    assert payload["capture_surface"] == "resident_app_bridge"

    queue = client.get("/app/ui-state/candidates")
    assert queue.status_code == 200
    assert queue.json()["kind"] == "resident_app_candidate_queue_screen_state"
    assert any(item["id"] == candidate_id for item in queue.json()["items"])

    detail = client.get(f"/app/ui-state/candidates/{candidate_id}")
    assert detail.status_code == 200
    assert detail.json()["kind"] == "resident_app_candidate_detail_screen_state"
    assert detail.json()["ui_summary"]["status"] == "pending"

    diff = client.get(f"/app/ui-state/candidates/{candidate_id}/diff")
    assert diff.status_code == 200
    assert diff.json()["review_surface"] == "resident_app_bridge"

    lineage = client.get(f"/app/ui-state/candidates/{candidate_id}/lineage")
    assert lineage.status_code == 200
    assert lineage.json()["candidate_id"] == candidate_id

    daemon = client.get("/app/ui-state/daemon")
    assert daemon.status_code == 200
    assert daemon.json()["kind"] == "resident_app_daemon_panel_screen_state"
    assert daemon.json()["operator_panels"][0]["panel"] == "packaging_status"
    assert daemon.json()["operator_phase_summary"]["phase_readiness"] == "not_ready_for_phase_closure"
    assert daemon.json()["operator_phase_details"]["workstreams"][0]["name"] == "packaging_model_decision"
    assert daemon.json()["service_target_summary"]["current_platform"] in {"macos", "linux", "windows", "other"}


def test_app_ui_action_review_flow_works_with_ui_cookie_session(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/ui-action/capture-clipboard",
        json={"content": "Resident app ui action review flow"},
    )
    assert capture.status_code == 200
    candidate_id = capture.json()["id"]

    evaluated = client.post(
        f"/app/ui-action/candidates/{candidate_id}/evaluate",
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "evaluated"

    approved = client.post(
        f"/app/ui-action/candidates/{candidate_id}/approve",
        json={"force_critical": False},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    from sayane.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("ui action review flow" in concept for concept in concepts)


def test_app_ui_approve_failure_returns_detail_with_error_feedback(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/ui/capture-clipboard",
        data={"content": "Resident app error path"},
        follow_redirects=False,
    )
    detail_path = capture.headers["location"]
    detail_base_path = detail_path.split("?", 1)[0]

    approve = client.post(
        detail_base_path + "/approve",
        data={},
        follow_redirects=False,
    )
    assert approve.status_code == 303
    assert "error=" in approve.headers["location"]

    error_page = client.get(approve.headers["location"])
    assert error_page.status_code == 200
    assert "This candidate is not in evaluated state and cannot be approved." in error_page.text


def test_app_ui_approve_failure_localizes_error_feedback_for_japanese_locale(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    bootstrap = client.get("/app/ui?locale=ja", headers=_auth(token))
    assert bootstrap.status_code == 200

    capture = client.post(
        "/app/ui/capture-clipboard",
        data={"content": "Resident app error path ja"},
        follow_redirects=False,
    )
    detail_path = capture.headers["location"]
    detail_base_path = detail_path.split("?", 1)[0]

    approve = client.post(
        detail_base_path + "/approve",
        data={},
        follow_redirects=False,
    )
    assert approve.status_code == 303

    error_page = client.get(approve.headers["location"])
    assert error_page.status_code == 200
    assert "この候補は評価済み状態ではないため承認できません。" in error_page.text


def test_app_ui_daemon_panel_html_with_ui_cookie_session(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env

    bootstrap = client.get("/app/ui", headers=_auth(token))
    assert bootstrap.status_code == 200

    daemon = client.get("/app/ui/daemon")
    assert daemon.status_code == 200
    assert "text/html" in daemon.headers["content-type"]
    assert "紗綾音 Resident App Daemon Panel" in daemon.text
    assert "Runtime Init Preview" in daemon.text
    assert "Next Actions" in daemon.text
    assert "Cleanup Preview" in daemon.text
    assert "Repair Preview" in daemon.text
    assert "Preview Hash" in daemon.text


def test_app_daemon_panel_screen_state_returns_framework_neutral_state(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.get("/app/screen-state/daemon", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_app_daemon_panel_screen_state"
    assert payload["summary_cards"][0]["key"] == "state"
    assert payload["operator_phase_summary"]["phase"] == "operator_packaging_and_supervision"
    assert payload["operator_phase_details"]["current_supported_operator_path"]["local_only"] is True
    assert payload["runtime_init"]["kind"] == "resident_daemon_runtime_init_plan"


def test_app_capture_clipboard_requires_auth(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, _ = bridge_env
    assert client.post("/app/capture-clipboard", json={"content": "hello"}).status_code == 401


def test_app_capture_clipboard_returns_candidate_payload(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    response = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "important_terms:\n  - \"Sayane\"", "locale": "ja"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "CandidateUpdate"
    assert payload["status"] == "pending"
    assert payload["capture_surface"] == "resident_app_bridge"
    assert payload["source"]["type"] == "clipboard"
    assert payload["capture_meta"]["capture_source"] == "clipboard"
    assert payload["locale"] == "ja"
    saved = config.candidates_dir / f"{payload['id']}.json"
    assert saved.exists()


def test_app_candidates_queue_returns_reviewable_items(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "New concept: resident app queue"},
    )
    assert capture.status_code == 200

    response = client.get("/app/candidates", headers=_auth(token))

    assert response.status_code == 200
    payload = response.json()
    assert payload["kind"] == "resident_app_candidate_queue"
    assert payload["is_review_surface"] is True
    assert payload["reviewable_count"] >= 1
    assert payload["status_counts"]["pending"] >= 1
    assert any(item["id"] == capture.json()["id"] for item in payload["items"])

    screen_state = client.get("/app/screen-state/candidates", headers=_auth(token))
    assert screen_state.status_code == 200
    screen_payload = screen_state.json()
    assert screen_payload["kind"] == "resident_app_candidate_queue_screen_state"
    assert screen_payload["status_counts"]["pending"] >= 1
    assert screen_payload["default_sort"] == "captured_at_desc"


def test_app_candidate_review_flow(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    capture = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "New concept: resident app review flow"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    detail = client.get(f"/app/candidates/{cid}", headers=_auth(token))
    assert detail.status_code == 200
    assert detail.json()["review_surface"] == "resident_app_bridge"
    assert detail.json()["ui_summary"]["status"] == "pending"
    assert detail.json()["allowed_actions"]["approve"] is False

    detail_state = client.get(f"/app/screen-state/candidates/{cid}", headers=_auth(token))
    assert detail_state.status_code == 200
    detail_state_payload = detail_state.json()
    assert detail_state_payload["kind"] == "resident_app_candidate_detail_screen_state"
    assert detail_state_payload["allowed_actions"]["approve"] is False
    assert detail_state_payload["ui_summary"]["status"] == "pending"
    assert detail_state_payload["ui_summary"]["source_type"] == "clipboard"

    diff = client.get(f"/app/candidates/{cid}/diff", headers=_auth(token))
    assert diff.status_code == 200
    assert diff.json()["review_surface"] == "resident_app_bridge"
    assert diff.json()["ui_summary"]["added_count"] >= 1
    assert "add" in diff.json()

    evaluated = client.post(
        f"/app/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "evaluated"
    assert evaluated.json()["review_surface"] == "resident_app_bridge"

    approved = client.post(
        f"/app/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["review_surface"] == "resident_app_bridge"

    from sayane.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("resident app review flow" in concept for concept in concepts)


def test_app_candidate_revise_flow(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "Original resident app text"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    revised = client.post(
        f"/app/candidates/{cid}/revise",
        headers=_auth(token),
        json={
            "edited_text": "Revised resident app text",
            "target_section": "knowledge.concepts",
            "change_reason": "clarified wording",
        },
    )

    assert revised.status_code == 200
    payload = revised.json()
    assert payload["review_surface"] == "resident_app_bridge"
    assert payload["status"] == "pending"
    assert payload["content"] == "Revised resident app text"
    assert payload["source"]["type"] == "candidate_revision"


def test_app_candidate_reject_flow(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/app/capture-clipboard",
        headers=_auth(token),
        json={"content": "Reject from app surface"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    rejected = client.post(
        f"/app/candidates/{cid}/reject",
        headers=_auth(token),
        json={"reason": "not needed"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"
    assert rejected.json()["review_surface"] == "resident_app_bridge"


def test_compile_via_post(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, token = bridge_env
    response = client.post(
        "/compile",
        headers=_auth(token),
        json={"target": "chatgpt", "profile_id": "default"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["target"] == "chatgpt"
    assert "messages" in body["payload"]


def test_context_packet_via_get(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, token = bridge_env
    response = client.get(
        "/context-packet",
        headers=_auth(token),
        params={"target": "claude", "profile": "default"},
    )
    assert response.status_code == 200
    assert response.json()["format"] == "anthropic_messages"


def test_capture_saves_candidate(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, config, token = bridge_env
    response = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "Selected text from page", "source": "selection"},
    )
    assert response.status_code == 200
    capture_id = response.json()["id"]
    saved = config.candidates_dir / f"{capture_id}.json"
    assert saved.exists()
    record = json.loads(saved.read_text(encoding="utf-8"))
    assert record["status"] in ("candidate", "pending")
    assert record["content"] == "Selected text from page"
    assert record["locale"] == "ja"


def test_capture_accepts_explicit_locale(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, config, token = bridge_env
    response = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "English context", "source": "selection", "locale": "en"},
    )
    assert response.status_code == 200
    capture_id = response.json()["id"]
    record = json.loads((config.candidates_dir / f"{capture_id}.json").read_text(encoding="utf-8"))
    assert record["locale"] == "en"


def test_capture_explicit_section_overrides_inference(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    content = "- Melotone: Edge AI\n"
    response = client.post(
        "/capture",
        headers=_auth(token),
        json={
            "content": content,
            "source": "selection",
            "section": "knowledge.concepts",
        },
    )
    assert response.status_code == 200
    assert response.json().get("warnings") == []
    record = json.loads(
        (config.candidates_dir / f"{response.json()['id']}.json").read_text(encoding="utf-8"),
    )
    assert record["proposal"]["section"] == "knowledge.concepts"


def test_capture_invalid_section_returns_400(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "text", "source": "test", "section": "identity.name"},
    )
    assert response.status_code == 400
    assert "Unknown proposal section" in response.json()["detail"]


def test_capture_structured_persona_returns_warnings(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    content = "person:\n  x: 1\nprojects:\n  y: 2\n"
    response = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": content, "source": "selection"},
    )
    assert response.status_code == 200
    assert response.json().get("warnings")


def test_capture_projects_infers_major_projects_and_marks_duplicates(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    profile_path = config.profiles_dir / "default" / "sayane.profile.yaml"
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8")
        + (
            "\nmajor_projects:\n"
            "  - name: \"Kotone\"\n"
            "    summary: \"宅内・エッジAI、PoP UID、個体管理、音声UI、Home Assistant統合\"\n"
            "  - name: \"Kotonoha\"\n"
            "    summary: \"AI協働・生成的監査・文脈継承基盤\"\n"
        ),
        encoding="utf-8",
    )
    content = (
        "major_projects:\n"
        "  - name: \"Kotone\"\n"
        "    summary: \"宅内・エッジAI、PoP UID、個体管理、音声UI、Home Assistant統合\"\n"
        "  - name: \"Kotonoha\"\n"
        "    summary: \"AI協働・生成的監査・文脈継承基盤\"\n"
    )
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": content, "source": "selection"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]
    detail = client.get(f"/candidates/{cid}", headers=_auth(token))
    proposal = detail.json()["proposal"]
    assert proposal["section"] == "major_projects"
    assert proposal["operation"] == "no_op_or_duplicate"
    assert proposal["items"] == []
    assert len(proposal["already_present"]) == 2
    assert proposal["add"] == []

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluation"]["rde_class"] == "Preserved"

    approved = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert approved.status_code == 400
    assert approved.json()["error"] == "unsafe_rde_category"
    assert approved.json()["rde_category"] == "Preserved"


def test_capture_communication_mode_duplicate_shows_non_recommended_diff(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    profile_path = config.profiles_dir / "default" / "sayane.profile.yaml"
    profile_path.write_text(
        profile_path.read_text(encoding="utf-8")
        + (
            "\ncommunication_mode:\n"
            "  assistant_name_for_chatgpt: \"ココリア\"\n"
            "  preferred_address: \"tomyukさん\"\n"
            "  intimate_address: \"ともゆきさん\"\n"
            "  collaboration_style:\n"
            "    - \"一緒に考える\"\n"
        ),
        encoding="utf-8",
    )
    content = (
        "communication_mode:\n"
        "  assistant_name_for_chatgpt: \"ココリア\"\n"
        "  preferred_address: \"tomyukさん\"\n"
        "  intimate_address: \"ともゆきさん\"\n"
        "  collaboration_style:\n"
        "    - \"一緒に考える\"\n"
    )
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": content, "source": "selection"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    detail = client.get(f"/candidates/{cid}", headers=_auth(token))
    proposal = detail.json()["proposal"]
    assert proposal["section"] == "communication_mode"
    assert proposal["operation"] == "no_op_or_duplicate"
    assert proposal["add"] == []
    assert proposal["items"] == []
    assert any(
        item["path"] == "communication_mode.assistant_name_for_chatgpt"
        for item in proposal["already_present"]
    )

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluation"]["rde_class"] == "Preserved"

    diff = client.get(f"/candidates/{cid}/diff", headers=_auth(token))
    body = diff.json()
    assert body["recommended_section"] == "communication_mode"
    assert body["has_duplicates"] is True
    assert body["profile_update_recommended"] is False


def test_communication_mode_content_misclassified_has_recommended_section(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    content = (
        "communication_mode:\n"
        "  assistant_name_for_chatgpt: \"ココリア\"\n"
        "  preferred_address: \"tomyukさん\"\n"
    )
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={
            "content": content,
            "source": "selection",
            "section": "knowledge.concepts",
        },
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]
    diff = client.get(f"/candidates/{cid}/diff", headers=_auth(token))
    body = diff.json()
    assert body["section"] == "knowledge.concepts"
    assert body["recommended_section"] == "communication_mode"
    assert body["profile_update_recommended"] is False


def test_invalid_token_rejected(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, _ = bridge_env
    response = client.get("/profiles", headers={"Authorization": "Bearer invalid"})
    assert response.status_code == 401


def test_candidate_evaluate_approve_flow(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "New concept: Bridge-driven evaluation flow", "source": "test"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    listed = client.get("/candidates", headers=_auth(token))
    assert listed.status_code == 200
    listed_items = listed.json()
    assert any(c["id"] == cid for c in listed_items)
    summary = next(c for c in listed_items if c["id"] == cid)
    assert "section" in summary
    assert isinstance(summary["section"], str)

    detail = client.get(f"/candidates/{cid}", headers=_auth(token))
    assert detail.status_code == 200
    assert detail.json()["id"] == cid

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "evaluated"
    assert evaluated.json()["evaluation"]["rde_class"]

    diff = client.get(f"/candidates/{cid}/diff", headers=_auth(token))
    assert diff.status_code == 200
    assert "add" in diff.json()

    approved = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    from sayane.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("Bridge-driven" in c for c in concepts)


def test_candidate_reject(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, config, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "Reject flow concept", "source": "test"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    rejected = client.post(
        f"/candidates/{cid}/reject",
        headers=_auth(token),
        json={"reason": "not needed"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"

    record = json.loads((config.candidates_dir / f"{cid}.json").read_text(encoding="utf-8"))
    assert record["status"] == "rejected"

    second_reject = client.post(
        f"/candidates/{cid}/reject",
        headers=_auth(token),
        json={"reason": "again"},
    )
    assert second_reject.status_code == 400
    assert second_reject.json()["error"] == "invalid_candidate_transition"


def test_candidate_voice_tone_approve_requires_force_critical(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={
            "content": "voice.tone:\n- collaborative and direct",
            "source": "test",
        },
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200

    denied = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert denied.status_code == 400
    raw = denied.json()
    body = raw.get("detail", raw)
    assert body["error"] == "requires_force_critical"
    assert body["section"] == "voice.tone"


def test_candidate_critical_approve_requires_force(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, config, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "values.core: must change core values", "source": "test"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluation"]["rde_class"] == "Critical Distortion"

    denied = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert denied.status_code == 400
    assert denied.json()["error"] == "unsafe_rde_category"
    assert denied.json()["rde_category"] == "Critical Distortion"

    from sayane.core.loader import load_profile

    profile_before = load_profile(config.profiles_dir / "default" / "sayane.profile.yaml")
    assert not any("must change" in v for v in profile_before.values.core)

    forced = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={
            "force_critical": True,
            "override_reason": "Reviewed manually after diff check",
        },
    )
    assert forced.status_code == 200
    assert forced.json()["status"] == "approved"


def test_candidate_transition_rules_for_final_states(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "final state guard check", "source": "test"},
    )
    cid = capture.json()["id"]
    approved = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert approved.status_code == 400
    assert approved.json()["error"] == "invalid_candidate_transition"

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    rejected = client.post(
        f"/candidates/{cid}/reject",
        headers=_auth(token),
        json={"reason": "stop"},
    )
    assert rejected.status_code == 200

    evaluate_again = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    approve_again = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert evaluate_again.status_code == 400
    assert evaluate_again.json()["error"] == "invalid_candidate_transition"
    assert approve_again.status_code == 400
    assert approve_again.json()["error"] == "invalid_candidate_transition"


@pytest.mark.parametrize(
    ("content", "expected_category"),
    [
        ("Expand docs with a new concept for retrieval evidence and lineage.", "Inferred Extension"),
        ("too short", "Unresolved Gap"),
        ("you must always rewrite every profile entry", "Suspicious Drift"),
        ("values.core must change right now", "Critical Distortion"),
    ],
)
def test_approve_category_safety_rules(
    bridge_env: tuple[TestClient, BridgeConfig, str],
    content: str,
    expected_category: str,
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": content, "source": "test"},
    )
    cid = capture.json()["id"]
    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["evaluation"]["rde_class"] == expected_category

    approved = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    if expected_category in {"Inferred Extension", "Authorized Transformation"}:
        assert approved.status_code == 200
        assert approved.json()["status"] == "approved"
    else:
        assert approved.status_code == 400
        assert approved.json()["error"] == "unsafe_rde_category"


def test_candidate_judge_auth_error_keeps_pending(
    bridge_env: tuple[TestClient, BridgeConfig, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client, _, token = bridge_env
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": "Judge auth failure simulation", "source": "test"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    def fake_load_judge_config(level: int) -> JudgeConfig | None:
        if level < 2:
            return None
        return JudgeConfig(
            base_url="https://api.openai.com/v1",
            api_key="dummy",
            model="gpt-4o-mini",
            timeout_sec=5.0,
        )

    def fake_review_with_llm(*_args, **_kwargs):
        raise LLMJudgeRequestError(
            message="LLM judge request failed: HTTP Error 401: Unauthorized",
            provider="openai",
            status_code=401,
        )

    monkeypatch.setattr(
        "sayane.evaluators.service.load_judge_config",
        fake_load_judge_config,
    )
    monkeypatch.setattr(
        "sayane.evaluators.service.review_with_llm",
        fake_review_with_llm,
    )

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 2},
    )
    assert evaluated.status_code == 200
    body = evaluated.json()
    # After judge failure, status is "evaluated" (heuristic level 1 preserved).
    assert body["status"] == "evaluated"
    assert body["evaluation_status"] == "judge_failed"
    assert body["evaluation"] is not None
    assert body["evaluation"]["rde_class"] is not None
    assert body["evaluation_error"]["type"] == "llm_judge_auth_error"
    assert body["evaluation_error"]["status_code"] == 401
    assert body["evaluation_error"]["provider"] == "openai"

    listed = client.get("/candidates", headers=_auth(token))
    summary = next(item for item in listed.json() if item["id"] == cid)
    assert summary["status"] == "evaluated"
    assert summary["evaluation_status"] == "judge_failed"


def test_important_terms_approve_requires_explicit_confirmation(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    content = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(
        encoding="utf-8",
    )
    capture = client.post(
        "/capture",
        headers=_auth(token),
        json={"content": content, "source": "clipboard", "section": "important_terms"},
    )
    assert capture.status_code == 200
    cid = capture.json()["id"]

    evaluated = client.post(
        f"/candidates/{cid}/evaluate",
        headers=_auth(token),
        json={"level": 1},
    )
    assert evaluated.status_code == 200
    assert evaluated.json()["status"] == "evaluated"

    denied = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={"force_critical": False},
    )
    assert denied.status_code == 400
    assert denied.json()["error"] == "explicit_confirmation_required"

    denied_reason = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={
            "force_critical": False,
            "explicit_confirmation": {
                "section": "important_terms",
                "checked": True,
                "reason": "   ",
            },
        },
    )
    assert denied_reason.status_code == 400
    assert denied_reason.json()["error"] == "explicit_confirmation_reason_required"

    approved = client.post(
        f"/candidates/{cid}/approve",
        headers=_auth(token),
        json={
            "force_critical": False,
            "explicit_confirmation": {
                "section": "important_terms",
                "checked": True,
                "reason": "差分を確認済み。",
            },
        },
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
