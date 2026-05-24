import json
import shutil
from pathlib import Path

from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


def test_mcp_list_profiles_cli(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    profile_dir = home / ".sayane" / "profiles" / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    result = runner.invoke(app, ["mcp", "list-profiles"])
    assert result.exit_code == 0, result.stdout + result.stderr
    data = json.loads(result.stdout)
    assert data[0]["id"] == "default"


def test_mcp_compile_cli(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    profile_dir = home / ".sayane" / "profiles" / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    result = runner.invoke(
        app,
        ["mcp", "compile", "--target", "chatgpt", "--profile-id", "default"],
    )
    assert result.exit_code == 0
    assert json.loads(result.stdout)["format"] == "openai_chat"


def test_mcp_inspect_profile_cli(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    profile_dir = home / ".sayane" / "profiles" / "default"
    profile_dir.mkdir(parents=True)
    shutil.copy(
        Path("examples/profiles/minimal.yaml"),
        profile_dir / "sayane.profile.yaml",
    )
    result = runner.invoke(app, ["mcp", "inspect-profile"])
    assert result.exit_code == 0
    assert json.loads(result.stdout)["identity"]["name"] == "Example User"
