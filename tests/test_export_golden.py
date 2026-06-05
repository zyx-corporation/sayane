"""Golden tests for markdown/prompt export fixtures (#145)."""
from pathlib import Path

from sayane.core.export import export_markdown, export_prompt
from sayane.core.loader import load_profile

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "export"


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def _golden(name: str) -> str:
    return FIXTURES.joinpath(name).read_text(encoding="utf-8").rstrip("\n")


def _assert_match(output: str, golden_name: str) -> None:
    assert output.rstrip("\n") == _golden(golden_name)


def test_markdown_identity_matches_golden():
    _assert_match(export_markdown(_profile(), ["identity"]), "identity.md")


def test_markdown_identity_interaction_matches_golden():
    _assert_match(export_markdown(_profile(), ["identity", "interaction"]), "identity-interaction.md")


def test_markdown_identity_interaction_technical_matches_golden():
    _assert_match(export_markdown(_profile(), ["identity", "interaction", "technical"]), "identity-interaction-technical.md")


def test_markdown_identity_interaction_technical_ethics_matches_golden():
    _assert_match(export_markdown(_profile(), ["identity", "interaction", "technical", "ethics"]), "identity-interaction-technical-ethics.md")


def test_prompt_identity_interaction_matches_golden():
    _assert_match(export_prompt(_profile(), ["identity", "interaction"]), "prompt-identity-interaction.txt")
