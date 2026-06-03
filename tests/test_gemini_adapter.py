"""Gemini adapter safety-oriented output tests."""

from sayane.adapters.claude import ClaudeAdapter
from sayane.adapters.gemini import GeminiAdapter
from sayane.core.models import PromptIR


def _ir_with_sensitive_markers() -> PromptIR:
    return PromptIR(
        system=[
            "You are assisting Example User.",
            "Default language: ja.",
            "system=制御面",
            "user=全文脈",
            "断定禁止",
            "ChatGPT=ココリア",
            "Claude=シオン",
        ],
        context=[
            "--- context/private/health.md ---\n"
            "Private health notes should not appear raw.\n",
            "--- context/notes/unverified.md ---\n"
            "Unverified employer division name\n",
            "--- context/projects.md ---\n"
            "Project Alpha: sample edge work\n",
        ],
        instruction=["Help with planning."],
        constraints=["Avoid: unsupported overclaiming."],
    )


def test_gemini_output_excludes_forbidden_phrases() -> None:
    text = GeminiAdapter().compile(_ir_with_sensitive_markers()).payload["text"]
    forbidden = (
        "system=制御面",
        "user=全文脈",
        "断定禁止",
        "context/private/health",
        "context/private/formation",
    )
    for phrase in forbidden:
        assert phrase not in text


def test_gemini_output_includes_safety_preamble() -> None:
    text = GeminiAdapter().compile(_ir_with_sensitive_markers()).payload["text"]
    assert "安全設定やシステム指示を上書きするものではありません" in text


def test_gemini_output_marks_unverified_section() -> None:
    text = GeminiAdapter().compile(_ir_with_sensitive_markers()).payload["text"]
    assert "## Unverified Notes" in text or "未確認情報" in text
    assert "Unverified employer" in text


def test_gemini_output_abstracts_private_context() -> None:
    text = GeminiAdapter().compile(_ir_with_sensitive_markers()).payload["text"]
    assert "Private health notes" not in text
    assert "個人的・機微な文脈" in text or "personal or sensitive" in text.lower()


def test_gemini_adapter_not_claude_template() -> None:
    ir = _ir_with_sensitive_markers()
    gemini = GeminiAdapter().compile(ir).payload["text"]
    claude_system = ClaudeAdapter().compile(ir).payload["system"]
    assert gemini != claude_system
    assert "anthropic_messages" == ClaudeAdapter().compile(ir).format
