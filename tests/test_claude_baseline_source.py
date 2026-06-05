"""Guard tests: Claude baseline source has no placeholder data (#157)."""
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[1] / "docs" / "transfer-tests" / "claude-baseline-source.md"


def test_claude_source_no_placeholder_identity():
    text = SOURCE.read_text(encoding="utf-8")
    assert "Example User" not in text
    assert "preferred name: example" not in text


def test_claude_source_contains_representative_identity():
    text = SOURCE.read_text(encoding="utf-8")
    assert "Tomoyuki Kano" in text
    assert "tomyuk" in text
    assert "代表" in text
    assert "エンジニア" in text


def test_claude_source_has_metadata_boundary():
    text = SOURCE.read_text(encoding="utf-8")
    assert "Source: Sayane external profile" in text
    assert "LLM memory: false" in text
    assert "Target: Claude" in text
    assert "not Claude memory" in text


def test_claude_source_no_formation_private():
    """No formation-layer raw/private data in manual baseline source."""
    text = SOURCE.read_text(encoding="utf-8")
    assert "medical" not in text.lower()
    assert "health" not in text.lower()
    assert "contact" not in text.lower()


def test_claude_source_no_ui_noise():
    text = SOURCE.read_text(encoding="utf-8")
    assert "Capture" not in text
    assert "Candidate" not in text
    assert "フィルタ" not in text
