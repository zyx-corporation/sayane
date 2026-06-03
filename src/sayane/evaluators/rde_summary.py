"""RDE summary messages aligned with diff + capture metadata."""

from __future__ import annotations

from typing import Any, Literal

from sayane.core.candidate import CandidateUpdate

CaptureSource = Literal["selection", "clipboard", "page"]

_MIXED_SECTIONS = "mixed_sections"
_REVIEW_REQUIRED = "review_required"
_PAGE_UI_WARNINGS = frozenset({"page_capture_low_confidence", "ui_noise_detected"})

MSG_MIXED_COMMON = "1件のCaptureに複数のProfile sectionが混在しています。"
MSG_MIXED_SELECTION_SUPPLEMENT = (
    "選択範囲に複数sectionが含まれているため、自動mergeせず確認が必要です。"
)
MSG_MIXED_PAGE_SUPPLEMENT = (
    "ページ全体CaptureにはUI文字列が混入する場合があるため、自動mergeせず確認が必要です。"
)

MSG_SUSPICIOUS_MIXED_SELECTION = (
    "この候補は、選択範囲内に複数種類のProfile sectionが混在しているため、"
    "疑わしい逸脱と評価されました。既存Profileとの重複やsection推定の誤りが疑われます。"
)
MSG_SUSPICIOUS_MIXED_PAGE = (
    "この候補は、ページ全体Capture由来のノイズを含み、複数種類の情報を"
    "単一sectionへ追加しようとしているため、疑わしい逸脱と評価されました。"
    "既存Profileとの重複やsection推定の誤りが疑われます。"
)
MSG_SUSPICIOUS_MIXED_PAGE_UI = (
    "この候補は、ページ全体Capture由来のUIノイズを含み、複数種類の情報を"
    "単一sectionへ追加しようとしているため、疑わしい逸脱と評価されました。"
    "既存Profileとの重複やsection推定の誤りが疑われます。"
)
MSG_SUSPICIOUS_CONCEPTS_VS_PROJECTS = (
    "project形式の項目が knowledge.concepts 向けに分類されていますが、"
    "推奨sectionは major_projects です。重複を確認してください。"
)
MSG_SUSPICIOUS_DUPLICATES = "既存Profileとの重複があり、そのままの採用は推奨されません。"
MSG_SUSPICIOUS_GENERIC = "疑わしい逸脱と評価されています。差分を確認してください。"
MSG_CRITICAL = "重大な歪曲と評価されています。原則として採用しないでください。"
MSG_PARSE_FAILED = (
    "この候補はYAMLとして解析できませんでした。"
    "選択範囲に改行崩れまたは構文エラーが含まれている可能性があります。"
    "Profileへ反映する前に内容を修正してください。"
)
MSG_SELECTION_PARSE_MIXED = (
    "この候補は、選択範囲Captureから取得されましたが、"
    "YAML構文が壊れているか、複数sectionが混在しているため、自動更新できません。"
    "Profileへ反映する前に、内容を修正して再Captureしてください。"
)


def capture_source_from_meta(meta: dict[str, Any]) -> CaptureSource:
    raw = meta.get("capture_source")
    if raw in ("selection", "clipboard", "page"):
        return raw
    if meta.get("user_selected"):
        return "selection"
    source = str(meta.get("source_type") or meta.get("source") or "").strip().lower()
    if source == "selection":
        return "selection"
    if source == "clipboard":
        return "clipboard"
    return "page"


def is_mixed_diff(section: str, recommended: str) -> bool:
    return section == _MIXED_SECTIONS or recommended == _REVIEW_REQUIRED


def should_mention_page_capture_noise(meta: dict[str, Any]) -> bool:
    """True when copy may refer to page-capture / UI noise (not selection-only)."""
    warnings = set(meta.get("capture_warnings") or [])
    source = capture_source_from_meta(meta)
    user_selected = bool(meta.get("user_selected"))

    if source in ("selection", "clipboard") or user_selected:
        return "ui_noise_detected" in warnings

    if source == "page" and not user_selected:
        return True

    return bool(warnings & _PAGE_UI_WARNINGS)


def mixed_section_supplement(meta: dict[str, Any]) -> str:
    source = capture_source_from_meta(meta)
    if source in ("selection", "clipboard") or meta.get("user_selected"):
        return MSG_MIXED_SELECTION_SUPPLEMENT
    return MSG_MIXED_PAGE_SUPPLEMENT


def build_rde_summary_message(
    candidate: CandidateUpdate,
    diff: dict[str, Any],
) -> str:
    """Human-readable RDE hint aligned with diff + capture_source."""
    evaluation = candidate.evaluation
    if evaluation is None:
        return ""
    rde = evaluation.rde_class
    section = str(diff.get("section", candidate.proposal.section))
    recommended = str(diff.get("recommended_section", section))
    meta = candidate.capture_meta.model_dump() if candidate.capture_meta else {}
    if candidate.source.type:
        meta.setdefault("source_type", candidate.source.type)
    mixed = is_mixed_diff(section, recommended)
    proposal = candidate.proposal
    parse_error = proposal.parse_error or (
        candidate.capture_meta.parse_error if candidate.capture_meta else None
    )

    if proposal.operation == "parse_failed" or parse_error:
        return MSG_PARSE_FAILED

    if rde == "Unresolved Gap":
        if section == _REVIEW_REQUIRED or proposal.operation == "parse_failed_or_no_effective_update":
            if capture_source_from_meta(meta) in ("selection", "clipboard"):
                return MSG_SELECTION_PARSE_MIXED
            return MSG_PARSE_FAILED

    if rde == "Suspicious Drift":
        if mixed:
            if capture_source_from_meta(meta) in ("selection", "clipboard") or meta.get(
                "user_selected",
            ):
                return MSG_SUSPICIOUS_MIXED_SELECTION
            if should_mention_page_capture_noise(meta):
                warnings = set(meta.get("capture_warnings") or [])
                if "ui_noise_detected" in warnings or "page_capture_low_confidence" in warnings:
                    return MSG_SUSPICIOUS_MIXED_PAGE_UI
                return MSG_SUSPICIOUS_MIXED_PAGE
            return MSG_SUSPICIOUS_MIXED_SELECTION
        if section == "knowledge.concepts" and recommended == "major_projects":
            return MSG_SUSPICIOUS_CONCEPTS_VS_PROJECTS
        if diff.get("has_duplicates") and not diff.get("profile_update_recommended"):
            return MSG_SUSPICIOUS_DUPLICATES
        return MSG_SUSPICIOUS_GENERIC
    if rde == "Critical Distortion":
        return MSG_CRITICAL
    return ""


def build_mixed_sections_detail(meta: dict[str, Any]) -> str:
    """Optional multi-line detail: common + capture_source supplement."""
    return f"{MSG_MIXED_COMMON}\n{mixed_section_supplement(meta)}"
