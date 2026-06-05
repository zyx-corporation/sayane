"""Tests for context export (#141)."""
from pathlib import Path

from sayane.core.export import export_markdown, export_prompt, export_yaml
from sayane.core.loader import load_profile


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def test_export_yaml_identity():
    output = export_yaml(_profile(), ["identity"])
    assert "name: Example User" in output
    assert "preferred_name: example" in output


def test_export_yaml_empty_scope():
    output = export_yaml(_profile(), ["unknown"])
    assert output.strip() == "{}"


def test_export_markdown_has_identity_section():
    output = export_markdown(_profile(), ["identity"], target="chatgpt")
    assert "## Identity" in output
    assert "Example User" in output
    assert "Target: chatgpt" in output


def test_export_markdown_scopes_header():
    output = export_markdown(_profile(), ["identity", "interaction"])
    assert "Scopes: identity, interaction" in output


def test_export_prompt_has_context_header():
    output = export_prompt(_profile(), ["identity"], target="generic")
    assert "[Context]" in output
    assert "Example User" in output


def test_export_prompt_excludes_identity_without_scope():
    output = export_prompt(_profile(), ["interaction"])
    assert "Example User" not in output
    assert "Language" in output


def test_export_markdown_default_target():
    output = export_markdown(_profile(), ["identity"])
    assert "Target: generic" in output
