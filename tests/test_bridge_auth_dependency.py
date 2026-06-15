from __future__ import annotations

from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from sayane.bridge.auth import BearerTokenAuth, load_or_create_token
from sayane.bridge.config import BridgeConfig


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_protected_route(app: FastAPI, auth: BearerTokenAuth) -> None:
    """Simulate route registration from a module outside create_app()."""

    @app.get("/protected")
    def protected(_: Annotated[None, Depends(auth)]) -> dict[str, bool]:
        return {"ok": True}


def test_bearer_token_auth_preserves_missing_header_error(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, BearerTokenAuth(config))
    client = TestClient(app)

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json() == {"detail": "Missing or invalid Authorization header"}


def test_bearer_token_auth_preserves_invalid_token_error(tmp_path: Path) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, BearerTokenAuth(config))
    client = TestClient(app)

    response = client.get("/protected", headers=_auth("invalid"))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid bearer token"}


def test_bearer_token_auth_accepts_valid_token_across_registration_boundary(
    tmp_path: Path,
) -> None:
    config = BridgeConfig(home=tmp_path / "sayane")
    token, _ = load_or_create_token(config)
    app = FastAPI()
    _register_protected_route(app, BearerTokenAuth(config))
    client = TestClient(app)

    response = client.get("/protected", headers=_auth(token))

    assert response.status_code == 200
    assert response.json() == {"ok": True}
