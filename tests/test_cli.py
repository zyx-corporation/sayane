import json
from pathlib import Path

import omomuki
from typer.testing import CliRunner

from omomuki.cli.main import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"omomuki {omomuki.__version__}"


def test_compile_chatgpt_from_example_profile(examples_dir: Path, tmp_path: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "chatgpt", "--profile", str(profile_path)],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["messages"][0]["role"] == "system"


def test_compile_claude_from_example_profile(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "claude", "--profile", str(profile_path)],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert "system" in payload


def test_profile_inspect(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(app, ["profile", "inspect", "--profile", str(profile_path)])
    assert result.exit_code == 0
    assert "Example User" in result.stdout
    assert "OmomukiProfile" in result.stdout


def test_init_creates_profile_store(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout + result.stderr
    profile_file = home / ".omomuki" / "profiles" / "default" / "omomuki.profile.yaml"
    assert profile_file.exists()


def test_export_markdown(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        [
            "export",
            "--format",
            "markdown",
            "--target",
            "chatgpt",
            "--profile",
            str(profile_path),
        ],
    )
    assert result.exit_code == 0
    assert "# Omomuki Compiled Prompt" in result.stdout
    assert "system" in result.stdout.lower()
