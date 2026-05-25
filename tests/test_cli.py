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


def test_compile_stdout_is_machine_readable_json(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "chatgpt", "--profile", str(profile_path)],
    )
    assert result.exit_code == 0, result.stdout + result.stderr
    assert result.stderr == ""
    payload = json.loads(result.stdout)
    assert "messages" in payload


def test_compile_unknown_target_has_actionable_error_and_no_stdout(
    examples_dir: Path,
) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "not-a-llm", "--profile", str(profile_path)],
    )
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "Unknown target" in result.stderr
    assert "Supported" in result.stderr
    assert "chatgpt" in result.stderr
    assert "claude" in result.stderr


def test_compile_missing_profile_has_recovery_hint(tmp_path: Path) -> None:
    missing = tmp_path / "no" / "such" / "file.yaml"
    result = runner.invoke(
        app,
        ["compile", "--target", "chatgpt", "--profile", str(missing)],
    )
    assert result.exit_code != 0
    assert result.stdout == ""
    assert "Profile not found" in result.stderr
    assert "sayane init" in result.stderr
    assert "--profile" in result.stderr


def test_profile_inspect(examples_dir: Path) -> None:
    profile_path = examples_dir / "profiles" / "minimal.yaml"
    result = runner.invoke(app, ["profile", "inspect", "--profile", str(profile_path)])
    assert result.exit_code == 0
    assert "Example User" in result.stdout
    assert "SayaneProfile" in result.stdout


def test_init_creates_profile_store(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0, result.stdout + result.stderr
    profile_file = home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    assert profile_file.exists()


def test_init_existing_store_is_non_destructive_and_explains_force(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0, first.stdout + first.stderr
    profile_file = home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    profile_file.write_text("sentinel", encoding="utf-8")

    second = runner.invoke(app, ["init"])

    assert second.exit_code == 0, second.stdout + second.stderr
    assert profile_file.read_text(encoding="utf-8") == "sentinel"
    assert "already exists" in second.stdout
    assert "--force" in second.stdout


def test_init_force_warns_on_stderr_before_overwrite(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    first = runner.invoke(app, ["init"])
    assert first.exit_code == 0, first.stdout + first.stderr
    profile_file = home / ".sayane" / "profiles" / "default" / "sayane.profile.yaml"
    profile_file.write_text("sentinel", encoding="utf-8")

    forced = runner.invoke(app, ["init", "--force"])

    assert forced.exit_code == 0, forced.stdout + forced.stderr
    assert "sentinel" not in profile_file.read_text(encoding="utf-8")
    assert "WARNING" in forced.stderr
    assert "Back up" in forced.stderr
    assert "Initialized" in forced.stdout


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


def test_storage_export_dry_run_lists_targets_without_writing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    home = tmp_path / "home"
    vault = tmp_path / "vault"
    vault.mkdir()
    monkeypatch.setenv("HOME", str(home))
    init_result = runner.invoke(app, ["init"])
    assert init_result.exit_code == 0, init_result.stdout + init_result.stderr

    result = runner.invoke(app, ["storage", "export", str(vault), "--dry-run"])

    assert result.exit_code == 0, result.stdout + result.stderr
    assert "sayane/MyContext.md" in result.stdout
    assert "Would export" in result.stdout
    assert not (vault / "sayane" / "MyContext.md").exists()
