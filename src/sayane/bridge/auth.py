"""Bridge bearer token management."""

import hashlib
import secrets

from sayane.bridge.config import BridgeConfig


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
