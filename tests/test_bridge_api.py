import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from omomuki.bridge.app import create_app
from omomuki.bridge.auth import load_or_create_token
from omomuki.bridge.config import BridgeConfig


@pytest.fixture
def bridge_env(tmp_path: Path) -> tuple[TestClient, BridgeConfig, str]:
    home = tmp_path / "omomuki"
    config = BridgeConfig(home=home)
    token, _ = load_or_create_token(config)

    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "omomuki.profile.yaml",
    )

    client = TestClient(create_app(config))
    return client, config, token


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_health_without_auth(bridge_env: tuple[TestClient, BridgeConfig, str]) -> None:
    client, _, _ = bridge_env
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
    assert any(c["id"] == cid for c in listed.json())

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

    from omomuki.core.loader import load_profile

    profile = load_profile(config.profiles_dir / "default" / "omomuki.profile.yaml")
    concepts = profile.knowledge.concepts if profile.knowledge else []
    assert any("Bridge-driven" in c for c in concepts)
