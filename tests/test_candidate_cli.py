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
