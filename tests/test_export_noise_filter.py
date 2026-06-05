"""Tests for export source hygiene / noise filtering (#155)."""
from pathlib import Path

from sayane.core.export import _clean_export_data, _is_noise_value, export_markdown
from sayane.core.loader import load_profile


def test_empty_string_is_noise():
    assert _is_noise_value("") is True
    assert _is_noise_value("   ") is True


def test_ui_label_is_noise():
    assert _is_noise_value("Capture") is True
    assert _is_noise_value("Candidate") is True
    assert _is_noise_value("Popup") is True
    assert _is_noise_value("このフィルタに該当する候補はありません") is True


def test_real_content_is_not_noise():
    assert _is_noise_value("RDE") is False
    assert _is_noise_value("Sayane") is False
    assert _is_noise_value("human dignity") is False
    assert _is_noise_value("Example User") is False


def test_noise_filtered_from_list():
    data = {"knowledge": {"concepts": ["RDE", "Capture", "", "Sayane", "Candidate"]}}
    cleaned = _clean_export_data(data)
    concepts = cleaned["knowledge"]["concepts"]
    assert "RDE" in concepts
    assert "Sayane" in concepts
    assert "Capture" not in concepts
    assert "Candidate" not in concepts


def test_duplicates_removed_from_list():
    data = {"important_terms": ["RDE", "Sayane", "RDE", "Sayane"]}
    cleaned = _clean_export_data(data)
    terms = cleaned["important_terms"]
    assert terms == ["RDE", "Sayane"]


def test_chatgpt_export_no_ui_noise():
    p = load_profile(Path("examples/profiles/minimal.yaml"))
    output = export_markdown(p, ["identity", "interaction", "technical"], target="chatgpt")
    assert "Capture" not in output
    assert "Candidate" not in output
    assert "Popup" not in output
    assert "Debug" not in output


def test_generic_export_no_ui_noise():
    p = load_profile(Path("examples/profiles/minimal.yaml"))
    output = export_markdown(p, ["identity", "interaction"], target="generic")
    assert "Capture" not in output
    assert "Candidate" not in output
