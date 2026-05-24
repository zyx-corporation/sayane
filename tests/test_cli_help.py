from typer.testing import CliRunner

from sayane.cli.main import app

runner = CliRunner()


def test_help_root_overview() -> None:
    result = runner.invoke(app, ["help"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "Sayane" in result.stdout
    assert "candidate" in result.stdout
    assert "profile" in result.stdout
    assert "evaluate" in result.stdout


def test_help_group_topic() -> None:
    result = runner.invoke(app, ["help", "candidate"])
    assert result.exit_code == 0, result.stdout + result.stderr
    assert "candidate" in (result.stdout + result.stderr).lower()


def test_help_nested_command_options() -> None:
    result = runner.invoke(app, ["help", "candidate", "evaluate"])
    assert result.exit_code == 0
    combined = (result.stdout + result.stderr).lower()
    assert "level" in combined


def test_help_nested_command() -> None:
    result = runner.invoke(app, ["help", "storage", "import"])
    assert result.exit_code == 0
    combined = (result.stdout + result.stderr).lower()
    assert "vault" in combined or "import" in combined


def test_help_unknown_topic() -> None:
    result = runner.invoke(app, ["help", "not-a-command"])
    assert result.exit_code != 0
