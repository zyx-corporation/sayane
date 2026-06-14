"""Tests for Local Vault unlock policy presets."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sayane.vault.contracts import SecretStoreAssurance
from sayane.vault.unlock_policy import (
    UnlockLevel,
    build_unlock_session_from_policy,
    default_unlock_policy,
)


def test_normal_policy_has_longer_timeout_and_read_context_scopes() -> None:
    policy = default_unlock_policy(UnlockLevel.NORMAL)

    assert policy.idle_timeout_seconds == 15 * 60
    assert policy.absolute_timeout_seconds == 60 * 60
    assert "profile:read" in policy.default_scopes
    assert "project_context:read" in policy.default_scopes
    assert "mcp:compiled_context" in policy.default_scopes
    assert "candidate:write" not in policy.default_scopes


def test_sensitive_policy_covers_candidate_review_lineage_scopes() -> None:
    policy = default_unlock_policy(UnlockLevel.SENSITIVE)

    assert policy.idle_timeout_seconds == 5 * 60
    assert policy.absolute_timeout_seconds == 15 * 60
    assert "candidate:read" in policy.default_scopes
    assert "candidate:write" in policy.default_scopes
    assert "review_decision:read" in policy.default_scopes
    assert "review_decision:write" in policy.default_scopes
    assert "lineage:read" in policy.default_scopes
    assert "lineage:write" in policy.default_scopes
    assert "deep_private:read" not in policy.default_scopes


def test_deep_private_policy_is_short_and_explicit() -> None:
    policy = default_unlock_policy(UnlockLevel.DEEP_PRIVATE)

    assert policy.idle_timeout_seconds == 3 * 60
    assert policy.absolute_timeout_seconds == 5 * 60
    assert policy.requires_explicit_unlock is True
    assert "deep_private:read" in policy.default_scopes
    assert "raw_capture:read" in policy.default_scopes
    assert "cloud_transfer_log:read" in policy.default_scopes
    assert "profile:read" not in policy.default_scopes


def test_build_unlock_session_from_policy_sets_idle_and_absolute_expiry() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    policy = default_unlock_policy(UnlockLevel.SENSITIVE)

    session = build_unlock_session_from_policy(
        session_id="s1",
        purpose="candidate review",
        assurance=SecretStoreAssurance.TEST_ONLY,
        policy=policy,
        now=now,
    )

    assert session.unlocked_at == now
    assert session.idle_expires_at == now + timedelta(seconds=5 * 60)
    assert session.expires_at == now + timedelta(seconds=15 * 60)
    assert session.allows("candidate:write") is True
    assert session.allows("deep_private:read") is False


def test_build_unlock_session_allows_scope_override() -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    policy = default_unlock_policy(UnlockLevel.NORMAL)

    session = build_unlock_session_from_policy(
        session_id="s1",
        purpose="narrow read",
        assurance=SecretStoreAssurance.TEST_ONLY,
        policy=policy,
        now=now,
        scopes=("profile:read",),
    )

    assert session.allows("profile:read") is True
    assert session.allows("mcp:compiled_context") is False
