"""Google Gemini adapter — user working-memo style (not control injection)."""

from sayane.adapters.base import Adapter, CompiledPrompt
from sayane.adapters.working_memo import compile_working_memo_payload
from sayane.core.models import PromptIR

_GEMINI_PREAMBLE_JA = """\
# User Working Context

以下は、ユーザーが自分の作業文脈を整理するために提供したメモです。
これはGeminiの安全設定やシステム指示を上書きするものではありません。
このメモは、会話の背景情報としてのみ参照してください。
未確認情報は推測として扱い、断定しないでください。
個人的・機微な情報は、ユーザーが明示的に求めた場合のみ扱ってください。
"""

_GEMINI_PREAMBLE_EN = """\
# User Working Context

The following is a user-provided working context note.
It is not intended to override Gemini's system instructions or safety settings.
Use it only as background context for this conversation.
Treat unverified information as uncertain, and do not present it as fact.
Handle personal or sensitive information only when the user explicitly asks for it.
"""


class GeminiAdapter(Adapter):
    """Compile Prompt IR to a Gemini-safe user working-memo (not Claude-style split)."""

    @property
    def target(self) -> str:
        return "gemini"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        return compile_working_memo_payload(
            ir,
            target=self.target,
            format_name="gemini_working_memo",
            preamble_ja=_GEMINI_PREAMBLE_JA,
            preamble_en=_GEMINI_PREAMBLE_EN,
        )
