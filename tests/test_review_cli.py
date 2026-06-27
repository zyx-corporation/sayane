from __future__ import annotations

import shutil
from pathlib import Path

from typer.testing import CliRunner

from sayane.bridge.config import BridgeConfig
from sayane.cli.main import app

runner = CliRunner()


def test_review_and_audit_with_vault_mode_use_vault_backed_store(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SAYANE_VAULT_PASSPHRASE", "cli-review-passphrase")
    config = BridgeConfig(home=home / ".sayane")
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )

    approve = runner.invoke(
        app,
        [
            "review",
            "approve",
            "vault-review-1",
            "--reason",
            "Approved in vault mode.",
            "--vault-mode",
            "development",
        ],
    )
    assert approve.exit_code == 0, approve.stdout
    assert "Decision recorded" in approve.stdout
    assert "derived from vault-backed review decisions" in approve.stdout
    assert not (config.home / "review_decisions" / "default.jsonl").exists()
    assert not (config.home / "audit" / "review-decisions.jsonl").exists()

    listed = runner.invoke(
        app,
        ["review", "list", "--vault-mode", "development"],
    )
    assert listed.exit_code == 0, listed.stdout
    assert "vault-review-1" in listed.stdout

    shown = runner.invoke(
        app,
        ["review", "show", "vault-review-1", "--vault-mode", "development"],
    )
    assert shown.exit_code == 0, shown.stdout
    assert "APPROVE" in shown.stdout

    audit_list = runner.invoke(
        app,
        ["audit", "list", "--vault-mode", "development"],
    )
    assert audit_list.exit_code == 0, audit_list.stdout
    assert "approve" in audit_list.stdout.lower()

    audit_export = runner.invoke(
        app,
        ["audit", "export", "--format", "json", "--vault-mode", "development"],
    )
    assert audit_export.exit_code == 0, audit_export.stdout
    assert "\"schema_version\": \"audit-export-v1\"" in audit_export.stdout
    assert "vault-review-1" in audit_export.stdout


def test_context_compile_with_vault_mode_reads_scoped_accept_decisions(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SAYANE_VAULT_PASSPHRASE", "cli-context-passphrase")
    config = BridgeConfig(home=home / ".sayane")
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )

    scoped = runner.invoke(
        app,
        [
            "review",
            "scoped-accept",
            "vault-scope-1",
            "--reason",
            "Scoped acceptance for vault-backed context.",
            "--scope",
            "project:demo:notes",
            "--vault-mode",
            "development",
        ],
    )
    assert scoped.exit_code == 0, scoped.stdout

    compiled = runner.invoke(
        app,
        ["context-compile", "--vault-mode", "development"],
    )
    assert compiled.exit_code == 0, compiled.stdout
    assert "vault-scope-1" in compiled.stdout
