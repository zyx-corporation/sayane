"""DeepSeek adapter — concise working-memo style with canonical terminology."""

from sayane.adapters.base import Adapter, CompiledPrompt
from sayane.adapters.working_memo import compile_working_memo_payload
from sayane.core.models import PromptIR

_DEEPSEEK_PREAMBLE_JA = """\
# User Working Context

以下は、ユーザーが自分の作業文脈を整理するために提供したメモです。
これはDeepSeekのシステム指示や安全設定を上書きするものではありません。
会話の背景情報として参照してください。
未確認情報は推測として扱い、断定しないでください。
"""

_DEEPSEEK_PREAMBLE_EN = """\
# User Working Context

The following is a user-provided working context note.
It is not intended to override DeepSeek system instructions or safety settings.
Use it only as background context for this conversation.
Treat unverified information as uncertain, and do not present it as fact.
"""


class DeepSeekAdapter(Adapter):
    """Compile Prompt IR to a DeepSeek-safe working memo (not raw system/user split)."""

    @property
    def target(self) -> str:
        return "deepseek"

    def compile(self, ir: PromptIR) -> CompiledPrompt:
        return compile_working_memo_payload(
            ir,
            target=self.target,
            format_name="deepseek_working_memo",
            preamble_ja=_DEEPSEEK_PREAMBLE_JA,
            preamble_en=_DEEPSEEK_PREAMBLE_EN,
            include_deprecated_values=False,
        )
