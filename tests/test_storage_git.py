import re
import subprocess
from pathlib import Path

from typer.testing import CliRunner

from sayane.cli.main import app
from sayane.storage.git_integration import commit_profile_store, is_git_repo


def _plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_git_commit_profile_store(tmp_path: Path) -> None:
    store = tmp_path / "profiles" / "default"
    store.mkdir(parents=True)
    (store / "sayane.profile.yaml").write_text("version: '0.1.0'\n", encoding="utf-8")
    ctx = store / "context"
    ctx.mkdir()
    (ctx / "note.md").write_text("# n\n", encoding="utf-8")

    commit_hash = commit_profile_store(store, "sayane: update context", init=True)
    assert commit_hash
    assert is_git_repo(store)

    result = subprocess.run(
        ["git", "log", "-1", "--oneline"],
        cwd=store,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "sayane" in result.stdout


def test_init_creates_git_repo(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout + result.stderr
    profile_dir = home / ".sayane" / "profiles" / "default"
    assert is_git_repo(profile_dir) is False
    assert "Committed" not in result.stdout and "コミット" not in result.stdout


def test_storage_index_auto_commits(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    runner.invoke(app, ["init"])
    profile_dir = home / ".sayane" / "profiles" / "default"
    ctx = profile_dir / "context"
    (ctx / "extra.md").write_text("# Extra\n", encoding="utf-8")

    result = runner.invoke(app, ["storage", "index"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert is_git_repo(profile_dir) is False


def test_storage_commit_requires_legacy_confirmation(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    runner.invoke(app, ["init"])

    result = runner.invoke(app, ["storage", "commit", "-m", "test commit", "--init"])
    assert result.exit_code != 0
    assert "--legacy-compatible" in _plain(result.stdout + result.stderr)


def test_storage_commit_with_legacy_confirmation_can_init_repo(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    runner = CliRunner()
    runner.invoke(app, ["init"])
    profile_dir = home / ".sayane" / "profiles" / "default"

    result = runner.invoke(
        app,
        ["storage", "commit", "-m", "test commit", "--init", "--legacy-compatible"],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert is_git_repo(profile_dir)
