"""Guard tests for formation-layer export policy (#148)."""
from pathlib import Path

from sayane.core.export import export_markdown, export_prompt, export_yaml
from sayane.core.loader import load_profile


def _profile():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def test_identity_scope_excludes_formation():
    """--scope identity should not leak formation-layer content."""
    output = export_markdown(_profile(), ["identity"])
    # Formation terms should not appear
    assert "formation" not in output.lower()


def test_prompt_excludes_formation_by_default():
    """Prompt export without formation scope excludes formation content."""
    output = export_prompt(_profile(), ["identity", "interaction"])
    assert "formation" not in output.lower()


def test_yaml_scope_filters_correctly():
    """YAML export only includes requested scopes."""
    output = export_yaml(_profile(), ["identity"])
    assert "identity" in output
    assert "voice" not in output  # voice is in interaction scope


def test_markdown_ethics_includes_values():
    """--scope ethics exports values and policy."""
    output = export_markdown(_profile(), ["ethics"])
    assert "Values" in output or "human dignity" in output
    assert "unsupported overclaiming" in output or "Policy" in output


def test_prompt_never_exports_email():
    """Prompt export must never include email/contact fields."""
    output = export_prompt(_profile(), ["identity", "interaction", "ethics"])
    assert "@" not in output  # No email addresses in prompt output
