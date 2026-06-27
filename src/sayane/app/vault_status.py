"""App-facing Local Vault status surface."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from sayane.app.runtime import ResidentRuntime
from sayane.vault.unlock_policy import UnlockLevel, default_unlock_policy


def build_app_vault_status(runtime: ResidentRuntime) -> dict[str, Any]:
    """Return a non-secret Local Vault status surface for app-facing UIs."""
    selection = runtime.repository_selection
    vault_runtime = selection.vault_runtime
    default_path = _default_vault_path(runtime.bridge_config.home)

    if vault_runtime is None:
        return {
            "kind": "resident_app_vault_status",
            "status": "unavailable",
            "backend": selection.backend.value,
            "storage_boundary": selection.storage_boundary,
            "vault_runtime_mode": None,
            "keychain_platform": None,
            "keychain_assurance": None,
            "supports_scoped_unlock_sessions": False,
            "vault_path": str(default_path),
            "recommended_setup": {
                "development": (
                    f"SAYANE_VAULT_PASSPHRASE=... sayane vault status --development --sqlite {default_path} "
                    "--passphrase-env SAYANE_VAULT_PASSPHRASE --json"
                ),
                "macos": (
                    f"sayane vault status --macos-keychain --sqlite {default_path} --json"
                ),
            },
            "unlock_policies": _unlock_policy_payloads(),
            "notes": [
                "resident runtime is currently using legacy process-local storage selection",
                "production vault default remains fail-closed until an explicit backend is selected",
            ],
        }

    caps = vault_runtime.keychain.capabilities()
    return {
        "kind": "resident_app_vault_status",
        "status": "available",
        "backend": selection.backend.value,
        "storage_boundary": selection.storage_boundary,
        "vault_runtime_mode": vault_runtime.mode.value,
        "vault_mode": vault_runtime.vault.mode().value,
        "keychain_platform": caps.platform_name,
        "keychain_assurance": caps.assurance.value,
        "supports_scoped_unlock_sessions": True,
        "supports_os_password_unlock": caps.supports_os_password_unlock,
        "supports_biometric_unlock": caps.supports_biometric_unlock,
        "vault_path": str(getattr(vault_runtime.vault, "path", default_path)),
        "unlock_policies": _unlock_policy_payloads(),
        "notes": list(caps.notes) + list(selection.notes),
    }


def _unlock_policy_payloads() -> list[dict[str, Any]]:
    policies: list[dict[str, Any]] = []
    for level in UnlockLevel:
        policy = default_unlock_policy(level)
        policies.append(
            {
                "level": level.value,
                "idle_timeout_seconds": policy.idle_timeout_seconds,
                "absolute_timeout_seconds": policy.absolute_timeout_seconds,
                "requires_explicit_unlock": policy.requires_explicit_unlock,
                "scopes": list(policy.default_scopes),
            }
        )
    return policies


def _default_vault_path(home: Path) -> Path:
    return home / "vault" / "main.sqlite"
