"""Resident app-facing Local Vault unlock-session status surfaces."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sayane.app.runtime import ResidentRuntime
from sayane.vault.unlock_policy import UnlockLevel, default_unlock_policy


def build_app_vault_session_status(runtime: ResidentRuntime) -> dict[str, Any]:
    """Return non-secret app-facing unlock-session state."""
    available_levels = [_policy_payload(level) for level in UnlockLevel]
    vault_runtime = runtime.vault_runtime
    backend = runtime.repository_selection.backend.value
    if vault_runtime is None:
        return {
            "kind": "resident_app_vault_session_status",
            "status": "unavailable",
            "backend": backend,
            "active_session_count": 0,
            "has_active_sessions": False,
            "active_sessions": [],
            "available_levels": available_levels,
            "notes": [
                "resident runtime is not connected to a Local Vault backend",
                "unlock sessions are process-local and require an explicit Local Vault runtime",
            ],
        }

    caps = vault_runtime.keychain.capabilities()
    manager = vault_runtime.session_manager
    now = datetime.now(UTC)
    active_sessions = [
        _session_payload(manager, session_id, session, now=now)
        for session_id, session in sorted(
            getattr(manager, "sessions", {}).items(),
            key=lambda item: item[1].expires_at,
        )
    ]
    return {
        "kind": "resident_app_vault_session_status",
        "status": "available",
        "backend": backend,
        "runtime_mode": vault_runtime.mode.value,
        "keychain_assurance": caps.assurance.value,
        "supports_scoped_unlock_sessions": True,
        "active_session_count": len(active_sessions),
        "has_active_sessions": bool(active_sessions),
        "active_sessions": active_sessions,
        "available_levels": available_levels,
        "notes": [
            "unlock sessions stay process-local to the resident Bridge runtime",
            "session metadata is app-readable, but key material remains outside app payloads",
        ],
    }


def _policy_payload(level: UnlockLevel) -> dict[str, Any]:
    policy = default_unlock_policy(level)
    return {
        "level": level.value,
        "idle_timeout_seconds": policy.idle_timeout_seconds,
        "absolute_timeout_seconds": policy.absolute_timeout_seconds,
        "default_scopes": list(policy.default_scopes),
        "requires_explicit_unlock": policy.requires_explicit_unlock,
    }


def _session_payload(
    manager: Any, session_id: str, session: Any, *, now: datetime
) -> dict[str, Any]:
    level = getattr(manager, "policy_levels", {}).get(session_id)
    return {
        "session_id": session.session_id,
        "purpose": session.purpose,
        "level": level.value if level is not None else None,
        "assurance": session.assurance.value,
        "scopes": list(session.scopes),
        "unlocked_at": session.unlocked_at.isoformat(),
        "idle_expires_at": session.idle_expires_at.isoformat() if session.idle_expires_at else None,
        "expires_at": session.expires_at.isoformat(),
        "is_expired": session.is_expired(now=now),
    }
