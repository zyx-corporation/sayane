import shutil
from pathlib import Path

from typer.testing import CliRunner

from sayane.bridge.config import BridgeConfig
from sayane.cli.main import app
from sayane.storage.candidates import create_from_capture

runner = CliRunner()


def test_candidate_list_and_evaluate(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config = BridgeConfig(home=home / ".sayane")
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    create_from_capture(config, "CLI test concept alpha", "test")

    result = runner.invoke(app, ["candidate", "list"])
    assert result.exit_code == 0
    assert "pending" in result.stdout or "evaluated" in result.stdout

    cid = config.candidates_dir.glob("*.json").__iter__().__next__().stem
    result = runner.invoke(app, ["candidate", "evaluate", cid])
    assert result.exit_code == 0
    assert "rde_class" in result.stdout


def test_candidate_commands_with_vault_mode_use_vault_backed_store(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SAYANE_VAULT_PASSPHRASE", "cli-candidate-passphrase")
    config = BridgeConfig(home=home / ".sayane")
    profile_dir = config.profiles_dir / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )

    capture = runner.invoke(
        app,
        [
            "capture",
            "--text",
            "CLI vault candidate alpha",
            "--vault-mode",
            "development",
        ],
    )
    assert capture.exit_code == 0, capture.stdout
    cid = next(
        line.split(":", 1)[1].strip()
        for line in capture.stdout.splitlines()
        if line.startswith("id:")
    )
    assert not (config.candidates_dir / f"{cid}.json").exists()

    listed = runner.invoke(app, ["candidate", "--vault-mode", "development", "list"])
    assert listed.exit_code == 0, listed.stdout
    assert cid in listed.stdout

    shown = runner.invoke(app, ["candidate", "--vault-mode", "development", "show", cid])
    assert shown.exit_code == 0, shown.stdout
    assert "CLI vault candidate alpha" in shown.stdout

    lineage = runner.invoke(
        app,
        ["candidate", "--vault-mode", "development", "lineage", "--profile-id", "default"],
    )
    assert lineage.exit_code == 0, lineage.stdout
    assert "candidate_generated" in lineage.stdout
