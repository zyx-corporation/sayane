"""Bridge bearer token management."""

from __future__ import annotations

import hashlib
import json
import secrets
from collections.abc import Callable
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, Request, status

from sayane.bridge.config import BridgeConfig


def _check_bearer(config: BridgeConfig, authorization: str | None) -> None:
    if authorization is None or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.removeprefix("Bearer ").strip()
    if not verify_token(config, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )


def create_bearer_dependency(config: BridgeConfig) -> Callable[..., None]:
    """Return a FastAPI dependency bound to a Bridge config."""

    def require_bearer(request: Request) -> None:
        _check_bearer(config, request.headers.get("authorization"))

    return require_bearer


class BearerTokenAuth:
    """Compatibility wrapper; prefer create_bearer_dependency for FastAPI."""

    def __init__(self, config: BridgeConfig) -> None:
        self.config = config

    def __call__(self, request: Request) -> None:
        _check_bearer(self.config, request.headers.get("authorization"))


@dataclass
class LocalUISession:
    """Dedicated UI session artifact for browser-driven resident app activity."""

    session_id: str
    token_hash: str
    issued_at: str
    expires_at: str


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


def issue_ui_session(config: BridgeConfig) -> str:
    """Mint and persist a dedicated local UI session token."""
    config.home.mkdir(parents=True, exist_ok=True)
    token = secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    expires_at = now + timedelta(seconds=config.ui_session_ttl_seconds)
    artifact = LocalUISession(
        session_id=secrets.token_hex(16),
        token_hash=_hash_ui_session_token(token),
        issued_at=now.isoformat(),
        expires_at=expires_at.isoformat(),
    )
    config.ui_session_file.write_text(json.dumps(asdict(artifact), indent=2), encoding="utf-8")
    config.ui_session_file.chmod(0o600)
    return token


def clear_ui_session(config: BridgeConfig) -> None:
    """Invalidate the current dedicated local UI session artifact."""
    config.ui_session_file.unlink(missing_ok=True)


def verify_ui_session(config: BridgeConfig, presented: str) -> bool:
    """Return whether the presented token matches the current dedicated local UI session."""
    if not presented:
        return False
    artifact = load_ui_session(config)
    if artifact is None:
        return False
    expires_at = datetime.fromisoformat(artifact.expires_at)
    if expires_at <= datetime.now(UTC):
        clear_ui_session(config)
        return False
    return secrets.compare_digest(_hash_ui_session_token(presented), artifact.token_hash)


def load_ui_session(config: BridgeConfig) -> LocalUISession | None:
    """Load the persisted dedicated local UI session artifact, if any."""
    path = config.ui_session_file
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return LocalUISession(**payload)


def _hash_ui_session_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def format_pairing_code(token: str) -> str:
    """Deterministic pairing hint derived from the bearer token."""
    digest = hashlib.sha256(token.encode()).digest()
    a = int.from_bytes(digest[0:2], "big") % 1000
    b = int.from_bytes(digest[2:4], "big") % 1000
    return f"{a:03d}-{b:03d}"
