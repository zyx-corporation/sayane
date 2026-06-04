import type { SupportedLocale } from "./types.js";
import { categoryLabel, type CandidateCategory } from "./candidate-display.js";

export type EvaluationNotePayload = {
  source?: "heuristic" | "llm_judge";
  key?: string | null;
  params?: Record<string, string | number | boolean | null>;
  text?: string | null;
};

const NOTE_MESSAGES: Record<SupportedLocale, Record<string, string>> = {
  ja: {
    content_references_critical_profile_fields:
      "重大なProfile項目または秘密情報への言及が検出されました。",
    identity_related_change_detected: "identity関連の変更が検出されました。",
    capture_too_short: "Captureが短すぎるため、信頼できる判断ができません。",
    multiple_profile_sections_mixed:
      "1件のCaptureに複数のProfile sectionが混在しています。",
    proposal_overlaps_existing_across_sections:
      "提案が既存Profileの複数sectionと重複しています。",
    imperative_or_overconfident_phrasing:
      "命令的または過度に断定的な表現が検出されました。",
    project_items_in_concepts:
      "project形式の項目が knowledge.concepts に含まれています。",
    potential_redundancy_with_major_projects:
      "既存の major_projects と重複している可能性があります。",
    no_effective_profile_update_major_projects:
      "既存の major_projects と重複しており、実質的な更新はありません。",
    project_updates_inferred: "Captureの構造から project 更新として推定しました。",
    no_effective_profile_update_communication_mode:
      "既存の communication_mode と重複しており、実質的な更新はありません。",
    communication_mode_requires_manual_review:
      "communication_mode の更新は手動確認が必要です。",
    communication_mode_values_in_concepts:
      "communication_mode 由来の値を knowledge.concepts に追加するべきではありません。",
    no_concrete_proposal_items: "具体的な提案項目が抽出されませんでした。",
    non_critical_knowledge_extension: "Captureから得られた非重大な知識補完です。",
    important_terms_list_add: "important_terms に {count} 件の追加候補があります。既存 {unchanged} 件は変更されません。",
    important_terms_no_change: "important_terms の項目はすべて既存Profileと一致しています。",
    proposal_adds_existing_projects:
      "既存プロジェクトを明確な理由なく再追加しようとしています。",
    potential_redundancy_in_concepts:
      "knowledge.concepts に重複が生じる可能性があります。",
    proposal_includes_existing_items:
      "既存Profileにすでに含まれる要素が提案に含まれています。",
    no_significant_new_information:
      "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。",
    proposal_includes_new_major_projects:
      "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。",
    potential_value_destructive_changes:
      "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。",
    ui_noise_detected:
      "ページ全体CaptureにUI文字列が含まれている可能性があります。",
    page_capture_low_confidence:
      "ページ全体Capture由来のため、低信頼入力として扱います。",
    llm_judge_result: "LLM judge（{model}）は「{rde_class_label}」と評価しました。",
    heuristic_merged_to_llm:
      "ヒューリスティック評価では「{heuristic_label}」でしたが、LLM judge結果を反映して「{rde_class_label}」に統合されました。",
    llm_judge_suggested_kept_heuristic:
      "LLM judgeは「{rde_class_label}」と評価しましたが、Sayaneのヒューリスティック評価「{heuristic_label}」を優先しました。",
    llm_judge_capped_important_terms_list_add:
      "LLM judgeは「{llm_rde_class_label}」と評価しましたが、important_terms の追加のみの差分のため「{rde_class_label}」を採用しました。用語名が未知でも、リスト追加だけでは疑わしい逸脱にはしません。",
    llm_judge_skipped: "LLM judgeはスキップされました: {detail}",
    llm_judge_failed: "LLM judgeに失敗しました: {detail}",
    llm_judge_freeform_prefix: "LLM judgeの指摘: {text}",
  },
  en: {
    content_references_critical_profile_fields:
      "Content references critical profile fields or secrets.",
    identity_related_change_detected: "Identity-related change detected.",
    capture_too_short: "Capture too short for reliable merge judgment.",
    multiple_profile_sections_mixed: "Multiple profile sections mixed in one capture.",
    proposal_overlaps_existing_across_sections:
      "Proposal overlaps existing profile entries across sections.",
    imperative_or_overconfident_phrasing: "Imperative or overconfident phrasing detected.",
    project_items_in_concepts: "Project-style items are included in knowledge.concepts.",
    potential_redundancy_with_major_projects:
      "The proposal may be redundant with existing major_projects.",
    no_effective_profile_update_major_projects:
      "No effective profile update: duplicate major_projects items.",
    project_updates_inferred: "Project updates inferred from capture structure.",
    no_effective_profile_update_communication_mode:
      "No effective profile update: duplicate communication_mode values.",
    communication_mode_requires_manual_review:
      "communication_mode updates require manual review.",
    communication_mode_values_in_concepts:
      "communication_mode-derived values should not be added to knowledge.concepts.",
    no_concrete_proposal_items: "No concrete proposal items extracted.",
    non_critical_knowledge_extension: "Non-critical knowledge extension from capture.",
    section_change_requires_manual_review: "Section change requires manual review.",
    proposal_adds_existing_projects:
      "Proposal adds existing projects without clear justification.",
    potential_redundancy_in_concepts: "Potential for redundancy in knowledge.concepts.",
    proposal_includes_existing_items:
      "The proposal includes elements already present in the profile.",
    no_significant_new_information:
      "No significant new information is added, which may reduce profile clarity.",
    proposal_includes_new_major_projects:
      "The proposal includes new major_projects that may shift the profile focus.",
    potential_value_destructive_changes:
      "The proposal may introduce value-destructive changes in the existing project context.",
    ui_noise_detected: "UI noise may be included in the page capture.",
    page_capture_low_confidence:
      "This candidate comes from a full-page capture and is treated as low-confidence input.",
    llm_judge_result: "LLM judge ({model}) classified this as {rde_class_label}.",
    heuristic_merged_to_llm:
      "Heuristic was {heuristic_label}; merged to {rde_class_label}.",
    llm_judge_suggested_kept_heuristic:
      "LLM judge suggested {rde_class_label}; kept heuristic {heuristic_label}.",
    llm_judge_capped_important_terms_list_add:
      "LLM judge classified this as {llm_rde_class_label}, but for an important_terms append-only list diff Sayane kept {rde_class_label}. Unfamiliar term names alone are not Suspicious Drift.",
    llm_judge_skipped: "LLM judge skipped: {detail}",
    llm_judge_failed: "LLM judge failed: {detail}",
    llm_judge_freeform_prefix: "LLM judge note: {text}",
  },
};

const LLM_NOTE_TRANSLATIONS: Record<SupportedLocale, Record<string, string>> = {
  ja: {
    "Proposal includes new major projects that may shift focus.":
      "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。",
    "Proposal includes new major_projects that may shift the profile focus.":
      "新しい major_projects を追加しようとしており、Profileの焦点を変える可能性があります。",
    "Potential for value-destructive changes in the context of existing projects.":
      "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。",
    "The proposal may introduce value-destructive changes in the existing project context.":
      "既存プロジェクト文脈に対して、価値を損なう変更になる可能性があります。",
    "Proposal includes elements that are already present in the profile, leading to potential redundancy.":
      "既存Profileにすでに含まれる要素が提案に含まれており、重複が生じる可能性があります。",
    "The proposal includes elements already present in the profile.":
      "既存Profileにすでに含まれる要素が提案に含まれています。",
    "No new significant information is added, which may dilute the clarity of the profile.":
      "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。",
    "No significant new information is added, which may reduce profile clarity.":
      "新しい重要情報は追加されておらず、Profileの明確性を下げる可能性があります。",
  },
  en: {},
};

const LEGACY_NOTE_KEYS: Record<string, string> = {
  "Content references critical profile fields or secrets.":
    "content_references_critical_profile_fields",
  "Identity-related change detected.": "identity_related_change_detected",
  "Capture too short for reliable merge judgment.": "capture_too_short",
  "Multiple profile sections mixed in one capture.": "multiple_profile_sections_mixed",
  "Proposal overlaps existing profile entries across sections.":
    "proposal_overlaps_existing_across_sections",
  "Imperative or overconfident phrasing detected.": "imperative_or_overconfident_phrasing",
  "Proposal contains project-style items in knowledge.concepts.": "project_items_in_concepts",
  "Potential redundancy with existing major_projects context.":
    "potential_redundancy_with_major_projects",
  "No effective profile update: duplicate major_projects items.":
    "no_effective_profile_update_major_projects",
  "Project updates inferred from capture structure.": "project_updates_inferred",
  "No effective profile update: duplicate communication_mode values.":
    "no_effective_profile_update_communication_mode",
  "communication_mode updates require manual review.": "communication_mode_requires_manual_review",
  "communication_mode-derived values should not be added to knowledge.concepts.":
    "communication_mode_values_in_concepts",
  "No concrete proposal items extracted.": "no_concrete_proposal_items",
  "Non-critical knowledge extension from capture.": "non_critical_knowledge_extension",
  "Section change requires manual review.": "section_change_requires_manual_review",
  "Proposal adds existing projects without clear justification.": "proposal_adds_existing_projects",
  "Potential for redundancy in knowledge.concepts.": "potential_redundancy_in_concepts",
};

function rdeClassLabel(value: string, locale: SupportedLocale): string {
  return categoryLabel(value as CandidateCategory, locale);
}

function formatTemplate(
  template: string,
  params: Record<string, string | number | boolean | null | undefined>,
  locale: SupportedLocale,
): string {
  const expanded: Record<string, string> = {};
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null) continue;
    expanded[key] = String(value);
  }
  if (expanded.rde_class) {
    expanded.rde_class_label = rdeClassLabel(expanded.rde_class, locale);
  }
  if (expanded.heuristic) {
    expanded.heuristic_label = rdeClassLabel(expanded.heuristic, locale);
  }
  if (expanded.llm_rde_class) {
    expanded.llm_rde_class_label = rdeClassLabel(expanded.llm_rde_class, locale);
  }
  return template.replace(/\{(\w+)\}/g, (_, name: string) => expanded[name] ?? `{${name}}`);
}

function coerceNote(note: string | EvaluationNotePayload): EvaluationNotePayload {
  if (typeof note !== "string") {
    return note;
  }
  const stripped = note.trim();
  const legacyKey = LEGACY_NOTE_KEYS[stripped];
  if (legacyKey) {
    return { source: "heuristic", key: legacyKey, params: {} };
  }
  const merged = stripped.match(/^Heuristic was (.+); merged to (.+)\.$/);
  if (merged) {
    return {
      source: "heuristic",
      key: "heuristic_merged_to_llm",
      params: { heuristic: merged[1], rde_class: merged[2] },
    };
  }
  const kept = stripped.match(/^LLM judge suggested (.+); kept heuristic (.+)\.$/);
  if (kept) {
    return {
      source: "heuristic",
      key: "llm_judge_suggested_kept_heuristic",
      params: { rde_class: kept[1], heuristic: kept[2] },
    };
  }
  const judge = stripped.match(/^LLM judge \((.+)\): (.+)$/);
  if (judge) {
    return {
      source: "llm_judge",
      key: "llm_judge_result",
      params: { model: judge[1], rde_class: judge[2] },
    };
  }
  return { source: "llm_judge", text: stripped };
}

export function formatEvaluationNote(
  note: string | EvaluationNotePayload,
  locale: SupportedLocale,
): string {
  const payload = coerceNote(note);
  if (payload.key) {
    const template =
      NOTE_MESSAGES[locale][payload.key] ?? NOTE_MESSAGES.en[payload.key];
    if (template) {
      return formatTemplate(template, payload.params ?? {}, locale);
    }
  }
  if (payload.text) {
    const translated = LLM_NOTE_TRANSLATIONS[locale][payload.text];
    if (translated) return translated;
    if (locale === "ja") {
      return formatTemplate(NOTE_MESSAGES.ja.llm_judge_freeform_prefix, { text: payload.text }, locale);
    }
    return payload.text;
  }
  return "";
}

export function formatEvaluationNotes(
  notes: Array<string | EvaluationNotePayload>,
  locale: SupportedLocale,
): string {
  const lines = notes
    .map((note) => formatEvaluationNote(note, locale))
    .filter((line) => line.length > 0);
  if (lines.length === 0) return "";
  return lines.map((line) => `- ${line}`).join("\n");
}
