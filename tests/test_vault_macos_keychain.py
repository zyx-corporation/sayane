"""Tests for explicit macOS keychain-backed Local Vault provider."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from sayane.vault.contracts import DataClass, SecretStoreAssurance, VaultStoreError
from sayane.vault.macos_keychain import (
    KEYCHAIN_SERVICE,
    MacOSKeychainProvider,
    SecurityCommandResult,
    build_sqlite_macos_vault_runtime,
)
from sayane.vault.unlock_policy import UnlockLevel


class FakeSecurityRunner:
    def __init__(self) -> None:
        self.secrets: dict[tuple[str, str], str] = {}
        self.calls: list[list[str]] = []

    def __call__(self, args: list[str]) -> SecurityCommandResult:
        self.calls.append(args)
        command = args[1]
        account = args[args.index("-a") + 1]
        service = args[args.index("-s") + 1]
        key = (service, account)
        if command == "find-generic-password":
            value = self.secrets.get(key)
            if value is None:
                return SecurityCommandResult(stdout="", stderr="not found", returncode=44)
            return SecurityCommandResult(stdout=value + "\n", stderr="", returncode=0)
        if command == "add-generic-password":
            self.secrets[key] = args[args.index("-w") + 1]
            return SecurityCommandResult(stdout="", stderr="", returncode=0)
        if command == "delete-generic-password":
            if key in self.secrets:
                del self.secrets[key]
                return SecurityCommandResult(stdout="", stderr="", returncode=0)
            return SecurityCommandResult(stdout="", stderr="not found", returncode=44)
        raise AssertionError(f"unexpected command: {args}")


@pytest.fixture
def darwin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("os.uname", lambda: type("Uname", (), {"sysname": "Darwin"})())


def test_macos_keychain_provider_creates_and_reuses_wrapping_secret(darwin) -> None:
    runner = FakeSecurityRunner()
    provider = MacOSKeychainProvider(command_runner=runner)

    first = provider.get_or_create_wrapping_secret("key-1")
    second = provider.get_or_create_wrapping_secret("key-1")

    assert first == second
    assert len(first) == 32
    assert runner.secrets[(KEYCHAIN_SERVICE, "key-1")] == base64.b64encode(first).decode("ascii")


def test_macos_keychain_provider_reports_os_backed_capabilities(darwin) -> None:
    provider = MacOSKeychainProvider(command_runner=FakeSecurityRunner())

    caps = provider.capabilities()

    assert caps.platform_name == "macos-keychain"
    assert caps.assurance == SecretStoreAssurance.OS_BACKED
    assert caps.supports_os_password_unlock is True


def test_macos_keychain_provider_opens_and_closes_unlock_session(darwin) -> None:
    provider = MacOSKeychainProvider(command_runner=FakeSecurityRunner())

    session = provider.unlock("test-purpose", ["candidate:key"])
    assert session.assurance == SecretStoreAssurance.OS_BACKED
    assert session.session_id in provider.active_sessions

    provider.lock(session.session_id)
    assert session.session_id not in provider.active_sessions


def test_macos_vault_runtime_round_trip(darwin, tmp_path: Path) -> None:
    runtime = build_sqlite_macos_vault_runtime(
        path=tmp_path / "vault.sqlite",
        profile_id="default",
        command_runner=FakeSecurityRunner(),
    )
    opener = getattr(runtime.session_manager, "open_policy_session")
    session = opener("macos-vault-test", UnlockLevel.SENSITIVE)

    saved = runtime.vault.put(
        data_class=DataClass.CANDIDATE,
        record_id="candidate-1",
        plaintext=b"macos secret",
        aad={"profile_id": "default", "record_type": "candidate"},
        session=session,
    )
    loaded = runtime.vault.get(
        data_class=DataClass.CANDIDATE,
        record_id="candidate-1",
        session=session,
    )

    assert runtime.mode.value == "production"
    assert runtime.vault.mode().value == "production"
    assert saved.algorithm == "AES-256-GCM"
    assert loaded == b"macos secret"


def test_macos_keychain_provider_rejects_non_macos(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("os.uname", lambda: type("Uname", (), {"sysname": "Linux"})())
    with pytest.raises(VaultStoreError, match="only available on macOS"):
        MacOSKeychainProvider(command_runner=FakeSecurityRunner())
