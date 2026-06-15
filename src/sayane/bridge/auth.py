"""Bridge bearer token management."""

from __future__ import annotations

import hashlib
import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from sayane.bridge.config import BridgeConfig


class BearerTokenAuth:
    """FastAPI dependency object for Bridge bearer-token authentication.

    This explicit dependency object is introduced for #178 so Bridge routes can
    cross module boundaries without depending on a closure-local function inside
    ``create_app``.

    It intentionally preserves the existing error status and detail strings used
    by the legacy ``require_bearer`` closure.
    """

    def __init__(self, config: BridgeConfig) -> None:
        self.config = config

    def __call__(
        self,
        authorization: Annotated[str | None, Header()] = None,
    ) -> None:
        if authorization is None or not authorization.startswith("Bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid Authorization header",
            )
        token = authorization.removeprefix("Bearer ").strip()
        if not verify_token(self.config, token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid bearer token",
            )


def load_or_create_token(config: BridgeConfig) -> tuple[str, bool]:
    """Load bearer token from disk, or create one. Returns (token, created)."""
    config.home.mkdir(parents=True, exist_ok=True)
    path = config.token_file
    if path.exists():
        return path.read_text(encoding="utf-8").strip(), False
    token = secrets.token_urlsafe(32)
    path.write_text(token, encoding="utf-8")
    path.chmod(0o600)
    return token, True


def load_token(config: BridgeConfig) -> str | None:
    path = config.token_file
    if not path.exists():
        return None
    return path.read_text(encoding="utf-8").strip()


def verify_token(config: BridgeConfig, presented: str) -> bool:
    expected = load_token(config)
    if expected is None or not presented:
        return False
    return secrets.compare_digest(presented, expected)


def format_pairing_code(token: str) -> str:
    """Deterministic pairing hint derived from the bearer token."""
    digest = hashlib.sha256(token.encode()).digest()
    a = int.from_bytes(digest[0:2], "big") % 1000
    b = int.from_bytes(digest[2:4], "big") % 1000
    return f"{a:03d}-{b:03d}"
