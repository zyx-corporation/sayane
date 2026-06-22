from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from sayane.bridge.auth import (
    clear_ui_session,
    create_bearer_dependency,
    issue_ui_session,
    load_or_create_token,
    verify_ui_session,
)
from sayane.bridge.config import BridgeConfig


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_protected_route(app: FastAPI, require_bearer: Callable[..., None]) -> None:
    """Simulate route registration from a module outside create_app()."""

    @app.get("/protected", dependencies=[Depends(require_bearer)])
    def protected() -> dict[str, bool]:
        return {"ok": True}


def test_bearer_dependency_preserves_missing_header_error(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, create_bearer_dependency(config))
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid Authorization header"}


def test_bearer_dependency_preserves_invalid_token_error(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, create_bearer_dependency(config))
    client = TestClient(app)

    response = client.get("/protected", headers=_auth("invalid"))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid bearer token"}


def test_bearer_dependency_accepts_valid_token_across_registration_boundary(
    tmp_path: Path,
) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    token, _ = load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, create_bearer_dependency(config))
    client = TestClient(app)

    response = client.get("/protected", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_dedicated_ui_session_verifies_and_replaces(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")

    first = issue_ui_session(config)
    assert verify_ui_session(config, first) is True

    second = issue_ui_session(config)
    assert verify_ui_session(config, first) is False
    assert verify_ui_session(config, second) is True


def test_dedicated_ui_session_can_be_cleared(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")

    token = issue_ui_session(config)
    assert verify_ui_session(config, token) is True

    clear_ui_session(config)
    assert verify_ui_session(config, token) is False
