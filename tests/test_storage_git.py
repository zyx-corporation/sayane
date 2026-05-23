import subprocess
from pathlib import Path

from typer.testing import CliRunner

from omomuki.cli.main import app
from omomuki.storage.git_integration import commit_profile_store, is_git_repo


def test_git_commit_profile_store(tmp_path: Path) -> None:
    store = tmp_path / "profiles" / "default"
    store.mkdir(parents=True)
    (store / "omomuki.profile.yaml").write_text("version: '0.1.0'\n", encoding="utf-8")
    ctx = store / "context"
    ctx.mkdir()
    (ctx / "note.md").write_text("# n\n", encoding="utf-8")

    commit_hash = commit_profile_store(store, "omomuki: update context", init=True)
    assert commit_hash
    assert is_git_repo(store)

    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=store,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "omomuki" in result.stdout


def test_init_creates_git_repo(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout + result.stderr
    profile_dir = home / ".omomuki" / "profiles" / "default"
    assert is_git_repo(profile_dir)
    assert "Committed" in result.stdout or "コミット" in result.stdout


def test_storage_index_auto_commits(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    runner.invoke(app, ["init"])
    profile_dir = home / ".omomuki" / "profiles" / "default"
    ctx = profile_dir / "context"
    (ctx / "extra.md").write_text("# Extra\n", encoding="utf-8")

    result = runner.invoke(app, ["storage", "index"])
    assert result.exit_code == 0, result.stdout + result.stderr

    log = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=profile_dir,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "storage index" in log.stdout
