import subprocess
from pathlib import Path

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
