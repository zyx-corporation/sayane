"""Tests for resident capability issuer hardening (#183)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from sayane.app.capabilities import (
    CapabilityError,
    CapabilityIssuer,
    create_local_capability_token,
)


def test_capability_issuer_adds_metadata_and_expiry() -> None:
    issued_at = datetime.now(UTC)
    issuer = CapabilityIssuer(issuer="resident-test", default_ttl_seconds=60)

    token = issuer.issue(
        ["capture"],
        subject="ui-session",
        purpose="clipboard_capture",
        issued_at=issued_at,
    )

    assert token.subject == "ui-session"
    assert token.issuer == "resident-test"
    assert token.purpose == "clipboard_capture"
    assert token.issued_at == issued_at
    assert token.expires_at == issued_at + timedelta(seconds=60)
    assert token.is_expired(now=issued_at) is False
    assert token.has("capture") is True


def test_expired_capability_token_fails_checks() -> None:
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_local_capability_token(
        ["capture"],
        issued_at=issued_at,
        ttl_seconds=0,
    )

    assert token.is_expired(now=issued_at) is True
    assert token.has("capture") is False
    with pytest.raises(CapabilityError, match="expired"):
        token.require("capture")


def test_capture_capability_does_not_imply_ui_mcp_or_admin() -> None:
    token = create_local_capability_token(["capture"])

    assert token.has("capture") is True
    assert token.has("ui") is False
    assert token.has("mcp") is False
    assert token.has("admin") is False


def test_mcp_capability_does_not_imply_ui_capture_or_admin() -> None:
    token = create_local_capability_token(["mcp"])

    assert token.has("mcp") is True
    assert token.has("ui") is False
    assert token.has("capture") is False
    assert token.has("admin") is False


def test_admin_capability_remains_explicit_override() -> None:
    token = create_local_capability_token(["admin"])

    assert token.has("admin") is True
    assert token.has("capture") is True
    assert token.has("ui") is True
    assert token.has("mcp") is True
    assert token.has("bridge") is True


def test_public_metadata_is_diagnostic_only() -> None:
    issued_at = datetime(2026, 1, 1, tzinfo=UTC)
    token = create_local_capability_token(
        ["capture"],
        subject="diagnostic-user",
        purpose="clipboard_capture",
        issuer="resident-test",
        issued_at=issued_at,
        ttl_seconds=60,
    )

    assert token.public_metadata() == {
        "subject": "diagnostic-user",
        "issuer": "resident-test",
        "purpose": "clipboard_capture",
        "scopes": ["capture"],
        "issued_at": "2026-01-01T00:00:00+00:00",
        "expires_at": "2026-01-01T00:01:00+00:00",
        "is_expired": True,
    }
