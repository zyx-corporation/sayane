import json
from pathlib import Path

from typer.testing import CliRunner

import sayane
from sayane.cli.main import app

runner = CliRunner()


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert result.stdout.strip() == f"sayane {sayane.__version__}"


def test_compile_chatgpt_from_example_profile(
    examples_dir: Path,
    tmp_path: Path,
) -> None:
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
    result = runner.invoke(
        app,
        ["profile", "inspect", "--profile", str(profile_path)],
    )
    assert result.exit_code == 0
    assert "Example User" in result.stdout
    assert "SayaneProfile" in result.stdout


def test_init_creates_profile_store(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout + result.stderr
    profile_file = (
        home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    )
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
    assert "# Sayane Compiled Prompt" in result.stdout
    assert "system" in result.stdout.lower()


def test_doctor_reports_missing_defaults(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SAYANE_JUDGE_BASE_URL", raising=False)
    monkeypatch.delenv("SAYANE_JUDGE_API_KEY", raising=False)
    monkeypatch.delenv("SAYANE_JUDGE_MODEL", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Bridge token: missing" in result.stdout
    assert "Profile store: missing" in result.stdout
    assert "Judge base URL: missing" in result.stdout
    assert "Judge API key: missing" in result.stdout
    assert "Judge model: missing" in result.stdout
    assert "OpenAI API key: missing" in result.stdout


def test_doctor_judge_topic_with_warning(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-openai-key")
    monkeypatch.setenv("SAYANE_JUDGE_BASE_URL", "https://api.openai.com/v1")
    monkeypatch.setenv("SAYANE_JUDGE_MODEL", "gpt-4.1-mini")
    monkeypatch.delenv("SAYANE_JUDGE_API_KEY", raising=False)
    result = runner.invoke(app, ["doctor", "judge"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Bridge token:" not in result.stdout
    assert "Profile store:" not in result.stdout
    assert "Judge base URL: set" in result.stdout
    assert "Judge API key: missing" in result.stdout
    assert "Judge model: set" in result.stdout
    assert "OpenAI API key: set" in result.stdout
    assert "SAYANE_JUDGE_API_KEY is missing" in result.stderr
