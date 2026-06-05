"""Tests for ChatGPT refined export (#153)."""
import re
from pathlib import Path

from sayane.core.export import export_markdown
from sayane.core.loader import load_profile


def _minimal():
    return load_profile(Path("examples/profiles/minimal.yaml"))


def _strip_ts(text: str) -> str:
    return re.sub(r"Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", "Generated: <TS>", text)


def test_chatgpt_includes_external_profile_metadata():
    output = export_markdown(_minimal(), ["identity"], target="chatgpt")
    assert "Sayane External Profile" in output
    assert "LLM memory: false" in output
    assert "Source: Sayane external profile" in output


def test_chatgpt_explicitly_not_llm_memory():
    output = export_markdown(_minimal(), ["identity"], target="chatgpt")
    assert "not ChatGPT memory" in output
    assert "external context supplied by Sayane" in output


def test_chatgpt_has_how_to_use_section():
    output = export_markdown(_minimal(), ["identity"], target="chatgpt")
    assert "How to Use This Context" in output


def test_chatgpt_philosophical_axioms_rendered_as_quote():
    output = export_markdown(_minimal(), ["identity", "ethics"], target="chatgpt")
    # values.core should appear as quoted axioms
    assert "Philosophical Stance" in output
    assert "Axiom 1" in output
    assert "Quote:" in output
    assert "Interpretation: not provided" in output


def test_chatgpt_no_invented_interpretation():
    output = export_markdown(_minimal(), ["identity", "ethics"], target="chatgpt")
    assert "Interpretation: not provided" in output
    # Should NOT contain invented interpretations
    assert "human dignity" in output  # the quote itself


def test_chatgpt_principles_from_knowledge():
    output = export_markdown(_minimal(), ["identity", "principles"], target="chatgpt")
    assert "Principles" in output
    assert "RDE" in output
    assert "Sayane" in output


def test_chatgpt_execution_context_when_projects_exist():
    from sayane.core.models import MajorProject
    p = load_profile(Path("examples/profiles/minimal.yaml"))
    p.major_projects = [
        MajorProject(name="Sayane", summary="context portability tool"),
        MajorProject(name="Kotone", summary="local-first AI foundation"),
    ]
    output = export_markdown(p, ["identity", "execution"], target="chatgpt")
    assert "Execution Context" in output
    assert "Sayane" in output
    assert "Kotone" in output


def test_chatgpt_export_policy_notes():
    output = export_markdown(_minimal(), ["identity"], target="chatgpt")
    assert "Export Policy Notes" in output
    assert "promptExport: never" in output


def test_chatgpt_no_ui_noise():
    output = export_markdown(_minimal(), ["identity", "interaction"], target="chatgpt")
    assert "Capture" not in output
    assert "Candidate" not in output
    assert "フィルタ" not in output
    assert "Popup" not in output
