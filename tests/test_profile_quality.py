from pathlib import Path

from sayane.core.loader import load_profile
from sayane.core.profile_quality import (
    capture_content_warnings,
    validate_profile_quality,
)


def test_capture_warns_on_structured_persona() -> None:
    content = "person:\n  name:\n    x: y\nprojects:\n  a:\n    b: c\n"
    warnings = capture_content_warnings(content)
    assert len(warnings) == 1
    assert "context" in warnings[0].lower()


def test_tone_yaml_line_warns(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    profile.voice.tone = ["name: Alex Chen"]
    warnings = validate_profile_quality(profile)
    assert any("voice.tone" in w and "YAML" in w for w in warnings)


def test_concepts_email_warns(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    assert profile.knowledge is not None
    profile.knowledge.concepts = ["alex@example.com"]
    warnings = validate_profile_quality(profile)
    assert any("PII" in w or "email" in w.lower() for w in warnings)


def test_clean_profile_no_warnings(examples_dir: Path) -> None:
    profile = load_profile(examples_dir / "profiles" / "minimal.yaml")
    assert validate_profile_quality(profile) == []
