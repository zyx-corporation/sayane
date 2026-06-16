"""Tests for resident capability issuer production-hardening seams (#186)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from sayane.app.capabilities import (
    CapabilityError,
    CapabilityIssuerPolicy,
    create_capability_issuer_for_surface,
    create_local_capability_token,
    create_surface_capability_tokens,
)
from sayane.app.runtime import build_resident_runtime


def test_capability_policy_defaults_are_local_and_non_persistent() -> None:
    policy = CapabilityIssuerPolicy()

    assert policy.public_metadata() == {
        "name": "local_development",
        "token_persistence": "non_persistent",
        "unlock_session_binding": "unbound",
        "network_auth": "not_supported",
        "cryptographic_signing": "not_supported",
        "production_ready": False,
    }


def test_persistent_capability_policy_is_rejected_for_now() -> None:
    policy = CapabilityIssuerPolicy(token_persistence="persistent")

    with pytest.raises(CapabilityError, match="persistent capability tokens"):
        create_local_capability_token(["capture"], policy=policy)


def test_surface_issuer_adds_surface_metadata_without_changing_token_metadata() -> None:
    issuer = create_capability_issuer_for_surface(
        "capture",
        issuer="local-test",
        default_ttl_seconds=None,
    )
    token = issuer.issue(
        ["capture"],
        issued_at=datetime(2026, 1, 1, tzinfo=UTC),
    )

    assert issuer.public_metadata() == {
        "issuer": "local-test:capture",
        "surface": "capture",
        "default_ttl_seconds": None,
        "policy": CapabilityIssuerPolicy().public_metadata(),
    }
    assert token.surface == "capture"
    assert token.policy.public_metadata() == CapabilityIssuerPolicy().public_metadata()
    assert token.public_metadata() == {
        "subject": "local_user",
        "issuer": "local-test:capture",
        "purpose": "resident_app",
        "scopes": ["capture"],
        "issued_at": "2026-01-01T00:00:00+00:00",
        "expires_at": None,
        "is_expired": False,
    }


def test_surface_capability_tokens_are_separate() -> None:
    tokens = create_surface_capability_tokens(issuer="local-test")

    assert sorted(tokens) == ["admin", "bridge", "capture", "mcp", "ui"]
    assert tokens["capture"].has("capture") is True
    assert tokens["capture"].has("ui") is False
    assert tokens["ui"].has("ui") is True
    assert tokens["ui"].has("mcp") is False
    assert tokens["mcp"].has("mcp") is True
    assert tokens["mcp"].has("bridge") is False
    assert tokens["bridge"].has("bridge") is True
    assert tokens["bridge"].has("capture") is False
    assert tokens["admin"].has("capture") is True
    assert tokens["admin"].has("mcp") is True


def test_runtime_tokens_are_surface_scoped_without_adding_bridge_token() -> None:
    runtime = build_resident_runtime()

    assert sorted(runtime.capabilities) == ["admin", "capture", "mcp", "ui"]
    assert runtime.capabilities["capture"].surface == "capture"
    assert runtime.capabilities["ui"].surface == "ui"
    assert runtime.capabilities["mcp"].surface == "mcp"
    assert runtime.capabilities["admin"].surface == "admin"
    assert runtime.capabilities["capture"].policy.token_persistence == "non_persistent"
    assert runtime.capabilities["capture"].policy.unlock_session_binding == "unbound"
