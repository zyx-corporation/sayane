from pathlib import Path

import pytest

from omomuki.storage.obsidian import (
    OMOMUKI_OBSIDIAN_VAULT_ENV,
    resolve_default_obsidian_vault,
    resolve_obsidian_vault,
)


def test_resolve_default_obsidian_vault_unset(monkeypatch) -> None:
    monkeypatch.delenv(OMOMUKI_OBSIDIAN_VAULT_ENV, raising=False)
    assert resolve_default_obsidian_vault() is None


def test_resolve_default_obsidian_vault_missing_dir(monkeypatch, tmp_path: Path) -> None:
    missing = tmp_path / "no-vault"
    monkeypatch.setenv(OMOMUKI_OBSIDIAN_VAULT_ENV, str(missing))
    assert resolve_default_obsidian_vault() is None


def test_resolve_default_obsidian_vault_expands_tilde(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv(OMOMUKI_OBSIDIAN_VAULT_ENV, "~/vault")
    assert resolve_default_obsidian_vault() == vault.resolve()


def test_resolve_obsidian_vault_explicit_arg(tmp_path: Path) -> None:
    vault = tmp_path / "explicit"
    vault.mkdir()
    assert resolve_obsidian_vault(vault) == vault


def test_resolve_obsidian_vault_from_env(monkeypatch, tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv(OMOMUKI_OBSIDIAN_VAULT_ENV, str(vault))
    assert resolve_obsidian_vault(None) == vault.resolve()


def test_resolve_obsidian_vault_raises_when_unset(monkeypatch) -> None:
    monkeypatch.delenv(OMOMUKI_OBSIDIAN_VAULT_ENV, raising=False)
    with pytest.raises(FileNotFoundError):
        resolve_obsidian_vault(None)
