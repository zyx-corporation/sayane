"""macOS Keychain-backed Local Vault runtime helpers.

This module keeps the OS-backed key release boundary explicit and opt-in.
It does not silently become the default production runtime; callers must
request the macOS keychain backend directly.
"""

from __future__ import annotations

import base64
import os
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

from sayane.storage.vault_bundle import build_vault_repository_bundle
from sayane.vault.contracts import (
    KeyCapabilities,
    PlatformKeychainProvider,
    SecretStoreAssurance,
    UnlockSession,
    VaultStoreError,
    VaultStoreMode,
)
from sayane.vault.development import (
    AesGcmCryptoProvider,
    SQLiteKeyringKeyManager,
)
from sayane.vault.factory import VaultRuntime
from sayane.vault.session import InMemoryUnlockSessionManager
from sayane.vault.sqlite_store import SQLiteVaultStore

KEYCHAIN_SERVICE = "com.sayane.local-vault"


@dataclass
class SecurityCommandResult:
    stdout: str
    stderr: str
    returncode: int


SecurityCommandRunner = callable


def _default_security_runner(args: list[str]) -> SecurityCommandResult:
    completed = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )
    return SecurityCommandResult(
        stdout=completed.stdout,
        stderr=completed.stderr,
        returncode=completed.returncode,
    )


@dataclass
class MacOSKeychainProvider(PlatformKeychainProvider):
    """OS-backed key release provider using the `security` CLI."""

    service_name: str = KEYCHAIN_SERVICE
    active_sessions: dict[str, UnlockSession] = field(default_factory=dict)
    command_runner: callable = _default_security_runner

    def __post_init__(self) -> None:
        if os.uname().sysname != "Darwin":
            raise VaultStoreError("macOS keychain provider is only available on macOS")

    def platform_name(self) -> str:
        return "macos-keychain"

    def capabilities(self) -> KeyCapabilities:
        return KeyCapabilities(
            platform_name=self.platform_name(),
            assurance=SecretStoreAssurance.OS_BACKED,
            supports_biometric_unlock=False,
            supports_os_password_unlock=True,
            supports_secure_enclave=False,
            supports_key_rotation=True,
            notes=[
                "uses macOS security CLI generic-password item storage",
                "opt-in production path; does not imply biometric gating yet",
            ],
        )

    def get_or_create_wrapping_secret(self, key_id: str) -> bytes:
        found = self._find_secret(key_id)
        if found is not None:
            return found
        secret = os.urandom(32)
        encoded = base64.b64encode(secret).decode("ascii")
        result = self.command_runner(
            [
                "security",
                "add-generic-password",
                "-a",
                key_id,
                "-s",
                self.service_name,
                "-w",
                encoded,
                "-U",
            ]
        )
        if result.returncode != 0:
            raise VaultStoreError(
                f"failed to store macOS keychain secret: {result.stderr.strip() or result.stdout.strip()}"
            )
        return secret

    def unlock(self, purpose: str, scopes: list[str]) -> UnlockSession:
        _ = self.get_or_create_wrapping_secret("local-vault-wrapping-key")
        now = datetime.now(UTC)
        session = UnlockSession(
            session_id=uuid4().hex,
            purpose=purpose,
            scopes=tuple(scopes),
            assurance=SecretStoreAssurance.OS_BACKED,
            unlocked_at=now,
            expires_at=now + timedelta(minutes=15),
            idle_expires_at=now + timedelta(minutes=5),
        )
        self.active_sessions[session.session_id] = session
        return session

    def lock(self, session_id: str) -> None:
        self.active_sessions.pop(session_id, None)

    def rotate_wrapping_secret(self, key_id: str) -> None:
        result = self.command_runner(
            [
                "security",
                "delete-generic-password",
                "-a",
                key_id,
                "-s",
                self.service_name,
            ]
        )
        if result.returncode not in (0, 44):
            raise VaultStoreError(
                f"failed to rotate macOS keychain secret: {result.stderr.strip() or result.stdout.strip()}"
            )
        self.get_or_create_wrapping_secret(key_id)

    def _find_secret(self, key_id: str) -> bytes | None:
        result = self.command_runner(
            [
                "security",
                "find-generic-password",
                "-a",
                key_id,
                "-s",
                self.service_name,
                "-w",
            ]
        )
        if result.returncode != 0:
            return None
        try:
            return base64.b64decode(result.stdout.strip().encode("ascii"))
        except Exception as exc:
            raise VaultStoreError("stored macOS keychain secret is not valid base64") from exc


def build_sqlite_macos_vault_runtime(
    *,
    path: Path,
    profile_id: str = "default",
    command_runner: callable = _default_security_runner,
) -> VaultRuntime:
    """Build an explicit macOS-keychain-backed SQLite Local Vault runtime."""
    keychain = MacOSKeychainProvider(command_runner=command_runner)
    session_manager = InMemoryUnlockSessionManager(keychain)
    key_manager = SQLiteKeyringKeyManager(path=path, keychain=keychain)
    crypto = AesGcmCryptoProvider(key_manager=key_manager)
    vault = SQLiteVaultStore(path=path, crypto=crypto, store_mode=VaultStoreMode.PRODUCTION)
    vault.initialize()
    repositories = build_vault_repository_bundle(vault, profile_id=profile_id)
    runtime = VaultRuntime(
        mode=VaultStoreMode.PRODUCTION,
        profile_id=profile_id,
        keychain=keychain,
        session_manager=session_manager,
        vault=vault,
        repositories=repositories,
    )
    runtime.require_not_test_only_for_production()
    return runtime
