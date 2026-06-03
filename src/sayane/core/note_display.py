"""Locale-aware display strings for evaluation notes."""

from __future__ import annotations

from typing import Any

from sayane.core.evaluation_notes import EvaluationNote

SupportedLocale = str

_RDE_CLASS_LABELS: dict[str, dict[str, str]] = {
    "ja": {
        "Preserved": "保存された要素",
        "Authorized Transformation": "許可された変換",
        "Inferred Extension": "推論による補完",
        "Unresolved Gap": "未解決の差分",
        "Suspicious Drift": "疑わしい逸脱",
        "Critical Distortion": "重大な歪曲",
    },
    "en": {
        "Preserved": "Preserved",
        "Authorized Transformation": "Authorized Transformation",
        "Inferred Extension": "Inferred Extension",
        "Unresolved Gap": "Unresolved Gap",
        "Suspicious Drift": "Suspicious Drift",
        "Critical Distortion": "Critical Distortion",
    },
}

_NOTE_MESSAGES: dict[str, dict[str, str]] = {
    "ja": {
        "content_references_critical_profile_fields": (
            "重大なProfile項目または秘密情報への言及が検出されました。"
        ),
        "identity_related_change_detected": "identity関連の変更が検出されました。",
        "capture_too_short": "Captureが短すぎるため、信頼できる判断ができません。",
        "multiple_profile_sections_mixed": (
            "1件のCaptureに複数のProfile sectionが混在しています。"
        ),
        "proposal_overlaps_existing_across_sections": (
            "提案が既存Profileの複数sectionと重複しています。"
        ),
        "imperative_or_overconfident_phrasing": (
            "命令的または過度に断定的な表現が検出されました。"
        ),
        "project_items_in_concepts": (
            "project形式の項目が knowledge.concepts に含まれています。"
        ),
        "potential_redundancy_with_major_projects": (
            "既存の major_projects と重複している可能性があります。"
        ),
        "no_effective_profile_update_major_projects": (
            "既存の major_projects と重複しており、実質的な更新はありません。"
        ),
        "project_updates_inferred": "Captureの構造から project 更新として推定しました。",
        "no_effective_profile_update_communication_mode": (
            "既存の communication_mode と重複しており、実質的な更新はありません。"
        ),
        "communication_mode_requires_manual_review": (
            "communication_mode の更新は手動確認が必要です。"
        ),
        "communication_mode_values_in_concepts": (
            "communication_mode 由来の値を knowledge.concepts に追加するべきではありません。"
        ),
        "no_concrete_proposal_items": "具体的な提案項目が抽出されませんでした。",
        "non_critical_knowledge_extension": (
            "Captureから得られた非重大な知識補完です。"
        ),
        "section_change_requires_manual_review": (
            "section変更には手動確認が必要です。"
        ),
        "proposal_adds_existing_projects": (
            "既存プロジェクトを明確な理由なく再追加しようとしています。"
        ),
        "potential_redundancy_in_concepts": (
            "knowledge.concepts に重複が生じる可能性があります。"
        ),
        "proposal_includes_existing_items": (
            "既存Profileにすでに含まれる要素が提案に含まれています。"
        ),
        "no_significant_new_information": (
            "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。"
        ),
        "proposal_includes_new_major_projects": (
            "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。"
        ),
        "potential_value_destructive_changes": (
            "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。"
        ),
        "ui_noise_detected": (
            "ページ全体CaptureにUI文字列が含まれている可能性があります。"
        ),
        "page_capture_low_confidence": (
            "ページ全体Capture由来のため、低信頼入力として扱います。"
        ),
        "llm_judge_result": (
            "LLM judge（{model}）は「{rde_class_label}」と評価しました。"
        ),
        "heuristic_merged_to_llm": (
            "ヒューリスティック評価では「{heuristic_label}」でしたが、"
            "LLM judge結果を反映して「{rde_class_label}」に統合されました。"
        ),
        "llm_judge_suggested_kept_heuristic": (
            "LLM judgeは「{rde_class_label}」と評価しましたが、"
            "Sayaneのヒューリスティック評価「{heuristic_label}」を優先しました。"
        ),
        "llm_judge_skipped": "LLM judgeはスキップされました: {detail}",
        "llm_judge_failed": "LLM judgeに失敗しました: {detail}",
        "llm_judge_freeform_prefix": "LLM judgeの指摘: {text}",
    },
    "en": {
        "content_references_critical_profile_fields": (
            "Content references critical profile fields or secrets."
        ),
        "identity_related_change_detected": "Identity-related change detected.",
        "capture_too_short": "Capture too short for reliable merge judgment.",
        "multiple_profile_sections_mixed": (
            "Multiple profile sections mixed in one capture."
        ),
        "proposal_overlaps_existing_across_sections": (
            "Proposal overlaps existing profile entries across sections."
        ),
        "imperative_or_overconfident_phrasing": (
            "Imperative or overconfident phrasing detected."
        ),
        "project_items_in_concepts": (
            "Project-style items are included in knowledge.concepts."
        ),
        "potential_redundancy_with_major_projects": (
            "The proposal may be redundant with existing major_projects."
        ),
        "no_effective_profile_update_major_projects": (
            "No effective profile update: duplicate major_projects items."
        ),
        "project_updates_inferred": (
            "Project updates inferred from capture structure."
        ),
        "no_effective_profile_update_communication_mode": (
            "No effective profile update: duplicate communication_mode values."
        ),
        "communication_mode_requires_manual_review": (
            "communication_mode updates require manual review."
        ),
        "communication_mode_values_in_concepts": (
            "communication_mode-derived values should not be added to "
            "knowledge.concepts."
        ),
        "no_concrete_proposal_items": "No concrete proposal items extracted.",
        "non_critical_knowledge_extension": (
            "Non-critical knowledge extension from capture."
        ),
        "section_change_requires_manual_review": (
            "Section change requires manual review."
        ),
        "proposal_adds_existing_projects": (
            "Proposal adds existing projects without clear justification."
        ),
        "potential_redundancy_in_concepts": (
            "Potential for redundancy in knowledge.concepts."
        ),
        "proposal_includes_existing_items": (
            "The proposal includes elements already present in the profile."
        ),
        "no_significant_new_information": (
            "No significant new information is added, which may reduce profile clarity."
        ),
        "proposal_includes_new_major_projects": (
            "The proposal includes new major_projects that may shift the profile focus."
        ),
        "potential_value_destructive_changes": (
            "The proposal may introduce value-destructive changes in the "
            "existing project context."
        ),
        "ui_noise_detected": "UI noise may be included in the page capture.",
        "page_capture_low_confidence": (
            "This candidate comes from a full-page capture and is treated as "
            "low-confidence input."
        ),
        "llm_judge_result": "LLM judge ({model}) classified this as {rde_class_label}.",
        "heuristic_merged_to_llm": (
            "Heuristic was {heuristic_label}; merged to {rde_class_label}."
        ),
        "llm_judge_suggested_kept_heuristic": (
            "LLM judge suggested {rde_class_label}; kept heuristic {heuristic_label}."
        ),
        "llm_judge_skipped": "LLM judge skipped: {detail}",
        "llm_judge_failed": "LLM judge failed: {detail}",
        "llm_judge_freeform_prefix": "LLM judge note: {text}",
    },
}

_LLM_NOTE_TRANSLATIONS: dict[str, dict[str, str]] = {
    "ja": {
        "Proposal includes new major projects that may shift focus.": (
            "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。"
        ),
        "Proposal includes new major_projects that may shift the profile focus.": (
            "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。"
        ),
        "Potential for value-destructive changes in the context of existing projects.": (
            "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。"
        ),
        "The proposal may introduce value-destructive changes in the "
        "existing project context.": (
            "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。"
        ),
        "Proposal includes elements that are already present in the profile, "
        "leading to potential redundancy.": (
            "既存Profileにすでに含まれる要素が提案に含まれており、重複が生じる可能性があります。"
        ),
        "The proposal includes elements already present in the profile.": (
            "既存Profileにすでに含まれる要素が提案に含まれています。"
        ),
        "No new significant information is added, which may dilute the clarity "
        "of the profile.": (
            "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。"
        ),
        "No significant new information is added, which may reduce profile clarity.": (
            "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。"
        ),
    },
    "en": {},
}


def _locale(locale: str | None) -> str:
    if locale and locale.startswith("ja"):
        return "ja"
    return "en"


def rde_class_label(rde_class: str, locale: str | None) -> str:
    loc = _locale(locale)
    return _RDE_CLASS_LABELS[loc].get(rde_class, rde_class)


def _format_template(template: str, params: dict[str, Any], locale: str) -> str:
    expanded = dict(params)
    for key in ("rde_class", "heuristic"):
        value = expanded.get(key)
        if isinstance(value, str):
            label_key = f"{key}_label" if key == "rde_class" else f"{key}_label"
            if key == "rde_class":
                expanded["rde_class_label"] = rde_class_label(value, locale)
            elif key == "heuristic":
                expanded["heuristic_label"] = rde_class_label(value, locale)
    try:
        return template.format(**expanded)
    except KeyError:
        return template


def format_evaluation_note(note: EvaluationNote, locale: str | None) -> str:
    loc = _locale(locale)
    if note.key:
        template = _NOTE_MESSAGES[loc].get(note.key) or _NOTE_MESSAGES["en"].get(note.key)
        if template:
            return _format_template(template, dict(note.params), loc)
    if note.text:
        translated = _LLM_NOTE_TRANSLATIONS[loc].get(note.text)
        if translated:
            return translated
        if loc == "ja":
            prefix = _NOTE_MESSAGES["ja"]["llm_judge_freeform_prefix"]
            return _format_template(prefix, {"text": note.text}, loc)
        return note.text
    return ""


def format_evaluation_notes(
    notes: list[EvaluationNote],
    locale: str | None,
) -> str:
    lines = [line for line in (format_evaluation_note(n, locale) for n in notes) if line]
    if not lines:
        return ""
    return "\n".join(f"- {line}" for line in lines)
