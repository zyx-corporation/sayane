"""Bridge preflight API (Capture-time preview, no Candidate)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml
from fastapi.testclient import TestClient

from sayane.bridge.app import create_app
from sayane.bridge.auth import load_or_create_token
from sayane.bridge.config import BridgeConfig


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


def _write_profile_important_terms(config: BridgeConfig, terms: list[str]) -> None:
    path = config.profiles_dir / "default" / "sayane.profile.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    data["important_terms"] = terms
    path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _terms_yaml(terms: list[str]) -> str:
    lines = ["important_terms:"]
    lines.extend(f'  - "{name}"' for name in terms)
    return "\n".join(lines) + "\n"


def test_preflight_important_terms_twelve_nine_three(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    """12 clipboard terms vs 9 saved → 9 existing, 3 added (Fixes #127)."""
    client, config, token = bridge_env
    existing = [f"term-{i:02d}" for i in range(1, 10)]
    clipboard = [*existing, "new-alpha", "new-beta", "new-gamma"]
    assert len(clipboard) == 12
    assert len(existing) == 9

    _write_profile_important_terms(config, existing)
    response = client.post(
        "/preflight/important-terms",
        headers=_auth(token),
        json={"content": _terms_yaml(clipboard), "profile_id": "default"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["section"] == "important_terms"
    assert body["total"] == 12
    assert body["existing_count"] == 9
    assert body["added_count"] == 3
    assert body["removed_count"] == 0


def test_preflight_important_terms_requires_section(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    client, _, token = bridge_env
    response = client.post(
        "/preflight/important-terms",
        headers=_auth(token),
        json={"content": "persona:\n  name: Example\n", "profile_id": "default"},
    )
    assert response.status_code == 400


def test_preflight_important_terms_xxx_yaml_shape(
    bridge_env: tuple[TestClient, BridgeConfig, str],
) -> None:
    """Regression: indented block from repo xxx.yaml (13 terms, 11 in profile)."""
    client, config, token = bridge_env
    content = (Path(__file__).resolve().parents[1] / "xxx.yaml").read_text(
        encoding="utf-8",
    )
    from sayane.evaluators.list_diff import parse_yaml_list_section

    proposed = parse_yaml_list_section(content, "important_terms")
    assert len(proposed) == 13

    from tests.test_list_diff import EXISTING

    _write_profile_important_terms(config, list(EXISTING))
    response = client.post(
        "/preflight/important-terms",
        headers=_auth(token),
        json={"content": content, "profile_id": "default"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 13
    assert body["existing_count"] == 11
    assert body["added_count"] == 2
