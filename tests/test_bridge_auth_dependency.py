from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from sayane.bridge.auth import create_bearer_dependency, load_or_create_token
from sayane.bridge.config import BridgeConfig


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _register_protected_route(app: FastAPI, require_bearer: Callable[..., None]) -> None:
    """Simulate route registration from a module outside create_app()."""

    @app.get("/protected")
    def protected(
        _: Annotated[None, Depends(require_bearer)] = None,
    ) -> dict[str, bool]:
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
