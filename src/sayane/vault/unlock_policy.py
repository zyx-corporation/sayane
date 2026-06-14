"""Unlock policy presets for Local Vault sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum

from sayane.vault.contracts import SecretStoreAssurance, UnlockSession


class UnlockLevel(StrEnum):
    """Human-facing unlock sensitivity levels."""

    NORMAL = "normal"
    SENSITIVE = "sensitive"
    DEEP_PRIVATE = "deep_private"


@dataclass(frozen=True)
class UnlockPolicy:
    """Timeout and default-scope policy for an unlock level."""

    level: UnlockLevel
    idle_timeout_seconds: int
    absolute_timeout_seconds: int
    default_scopes: tuple[str, ...]
    requires_explicit_unlock: bool = True


def default_unlock_policy(level: UnlockLevel) -> UnlockPolicy:
    """Return the default ADR 0001 unlock policy for a level."""
    if level == UnlockLevel.NORMAL:
        return UnlockPolicy(
            level=level,
            idle_timeout_seconds=15 * 60,
            absolute_timeout_seconds=60 * 60,
            default_scopes=(
                "profile:read",
                "project_context:read",
                "mcp:compiled_context",
            ),
            requires_explicit_unlock=False,
        )
    if level == UnlockLevel.SENSITIVE:
        return UnlockPolicy(
            level=level,
            idle_timeout_seconds=5 * 60,
            absolute_timeout_seconds=15 * 60,
            default_scopes=(
                "candidate:read",
                "candidate:write",
                "candidate:key",
                "review_decision:read",
                "review_decision:write",
                "review_decision:key",
                "lineage:read",
                "lineage:write",
                "lineage:key",
            ),
        )
    if level == UnlockLevel.DEEP_PRIVATE:
        return UnlockPolicy(
            level=level,
            idle_timeout_seconds=3 * 60,
            absolute_timeout_seconds=5 * 60,
            default_scopes=(
                "deep_private:read",
                "raw_capture:read",
                "cloud_transfer_log:read",
            ),
        )
    raise ValueError(f"unknown unlock level: {level}")


def build_unlock_session_from_policy(
    *,
    session_id: str,
    purpose: str,
    policy: UnlockPolicy,
    assurance: SecretStoreAssurance,
    now: datetime | None = None,
    scopes: tuple[str, ...] | None = None,
) -> UnlockSession:
    """Build an UnlockSession using one policy preset."""
    started_at = now or datetime.now(UTC)
    return UnlockSession(
        session_id=session_id,
        purpose=purpose,
        scopes=scopes or policy.default_scopes,
        assurance=assurance,
        unlocked_at=started_at,
        expires_at=started_at + timedelta(seconds=policy.absolute_timeout_seconds),
        idle_expires_at=started_at + timedelta(seconds=policy.idle_timeout_seconds),
    )
