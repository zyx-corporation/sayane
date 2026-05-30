import json
from pathlib import Path

from typer.testing import CliRunner

from sayane.bridge.config import BridgeConfig
from sayane.cli.main import app

runner = CliRunner()


def test_capture_from_text(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config = BridgeConfig(home=home / ".sayane")

    result = runner.invoke(
        app,
        ["capture", "--text", "CLI capture concept beta", "--source", "cli-test"],
    )
    assert result.exit_code == 0, result.stdout
    assert "id:" in result.stdout
    assert list(config.candidates_dir.glob("*.json"))


def test_capture_from_stdin(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    result = runner.invoke(app, ["capture", "--json"], input="stdin capture line\n")
    assert result.exit_code == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["status"] == "captured"
    assert payload["id"]


def test_capture_from_file(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))
    config = BridgeConfig(home=home / ".sayane")
    capture_file = tmp_path / "note.txt"
    capture_file.write_text("file capture content", encoding="utf-8")

    result = runner.invoke(app, ["capture", "--file", str(capture_file)])
    assert result.exit_code == 0, result.stdout
    cid = next(line.split(":", 1)[1].strip() for line in result.stdout.splitlines() if line.startswith("id:"))
    saved = json.loads((config.candidates_dir / f"{cid}.json").read_text(encoding="utf-8"))
    assert "file capture content" in saved["content"]


def test_capture_requires_input(tmp_path: Path, monkeypatch) -> None:
    home = tmp_path / "home"
    monkeypatch.setenv("HOME", str(home))

    result = runner.invoke(app, ["capture"])
    assert result.exit_code == 2
