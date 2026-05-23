from typer.testing import CliRunner

from omomuki.cli.app import build_app
from omomuki.cli.i18n import init_locale_from_argv, set_locale


def test_init_locale_from_argv() -> None:
    assert init_locale_from_argv(["--lang", "ja", "help"]) == "ja"
    set_locale("en")


def test_help_japanese() -> None:
    set_locale("ja")
    runner = CliRunner()
    result = runner.invoke(build_app(), ["help"])
    assert result.exit_code == 0
    assert "使い方" in result.stdout
    assert "グループ" in result.stdout
    set_locale("en")


def test_candidate_none_message_japanese(tmp_path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    set_locale("ja")
    runner = CliRunner()
    result = runner.invoke(build_app(), ["candidate", "list"])
    assert result.exit_code == 0
    assert "Candidate がありません" in result.stdout
    set_locale("en")
