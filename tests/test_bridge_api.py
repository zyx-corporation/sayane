import json
import shutil
from pathlib import Path

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
    assert body["status"] == "pending"
    assert body["evaluation_status"] == "judge_failed"
    assert body["evaluation"] is None
    assert body["evaluation_error"]["type"] == "llm_judge_auth_error"
    assert body["evaluation_error"]["status_code"] == 401
    assert body["evaluation_error"]["provider"] == "openai"

    listed = client.get("/candidates", headers=_auth(token))
    summary = next(item for item in listed.json() if item["id"] == cid)
    assert summary["status"] == "pending"
    assert summary["evaluation_status"] == "judge_failed"
