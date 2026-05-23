from pathlib import Path

from typer.testing import CliRunner

from omomuki.cli.main import app

runner = CliRunner()


def test_storage_index_updates_profile(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner.invoke(app, ["init"])
    ctx = home / ".omomuki" / "profiles" / "default" / "context"
    (ctx / "extra.md").write_text("# Extra\n", encoding="utf-8")

    result = runner.invoke(app, ["storage", "index"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "entries:" in result.stdout


def test_storage_import_dry_run(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "from-vault.md").write_text("# V\n", encoding="utf-8")

    runner.invoke(app, ["init"])
    result = runner.invoke(
        app,
        ["storage", "import", str(vault), "--dry-run"],
    )
    assert result.exit_code == 0
    assert "from-vault.md" in result.stdout


def test_storage_import_uses_obsidian_vault_env(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "env-note.md").write_text("# Env\n", encoding="utf-8")
    monkeypatch.setenv("OMOMUKI_OBSIDIAN_VAULT", str(vault))

    runner.invoke(app, ["init"])
    result = runner.invoke(app, ["storage", "import", "--dry-run"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "env-note.md" in result.stdout
