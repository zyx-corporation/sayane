/** RDE / section summary for diff viewer (derived from current diff payload). */

import type { CandidateDetail, SupportedLocale } from "./types.js";

export type DiffPayload = Record<string, unknown>;

export type CaptureMetaView = {
  capture_source?: "selection" | "clipboard" | "page";
  user_selected?: boolean;
  capture_confidence?: string;
  capture_warnings?: string[];
};

const PAGE_UI_WARNINGS = new Set(["page_capture_low_confidence", "ui_noise_detected"]);

function captureMeta(candidate: CandidateDetail): CaptureMetaView {
  const meta = (candidate as CandidateDetail & { capture_meta?: CaptureMetaView }).capture_meta;
  const sourceType = typeof candidate.source === "string" ? candidate.source : "";
  return {
    ...meta,
    source_type: sourceType,
  } as CaptureMetaView & { source_type?: string };
}

export function captureSourceFromMeta(meta: CaptureMetaView & { source_type?: string }): "selection" | "clipboard" | "page" {
  if (
    meta.capture_source === "selection"
    || meta.capture_source === "clipboard"
    || meta.capture_source === "page"
  ) {
    return meta.capture_source;
  }
  if (meta.user_selected) return "selection";
  if (meta.source_type === "selection") return "selection";
  if (meta.source_type === "clipboard") return "clipboard";
  return "page";
}

export function isMixedDiff(diff: DiffPayload, candidate: CandidateDetail): boolean {
  const section = String(diff.section ?? candidate.proposal.section ?? "");
  const recommended = String(diff.recommended_section ?? section);
  return section === "mixed_sections" || recommended === "review_required";
}

export function shouldMentionPageCaptureNoise(meta: CaptureMetaView & { source_type?: string }): boolean {
  const warnings = new Set(meta.capture_warnings ?? []);
  const source = captureSourceFromMeta(meta);
  const userSelected = Boolean(meta.user_selected);

  if (source === "selection" || source === "clipboard" || userSelected) {
    return warnings.has("ui_noise_detected");
  }
  if (source === "page" && !userSelected) {
    return [...warnings].some((w) => PAGE_UI_WARNINGS.has(w)) || true;
  }
  return [...warnings].some((w) => PAGE_UI_WARNINGS.has(w));
}

const JA = {
  suspiciousMixedSelection:
    "この候補は、選択範囲内に複数種類のProfile sectionが混在しているため、疑わしい逸脱と評価されました。既存Profileとの重複やsection推定の誤りが疑われます。",
  suspiciousMixedPage:
    "この候補は、ページ全体Capture由来のノイズを含み、複数種類の情報を単一sectionへ追加しようとしているため、疑わしい逸脱と評価されました。既存Profileとの重複やsection推定の誤りが疑われます。",
  suspiciousConceptsVsProjects:
    "この候補は、project形式の項目を knowledge.concepts へ追加しようとしている一方、推奨sectionは major_projects です。既存Profileとの重複が疑われます。",
  suspiciousDuplicates:
    "疑わしい逸脱と評価されています。既存Profileに重複する項目があり、そのままの採用は推奨されません。",
  suspiciousGeneric: "疑わしい逸脱と評価されています。差分を確認してから判断してください。",
  critical:
    "この候補は「重大な歪曲」と評価されています。原則として採用せず、棄却または修正候補の作成を検討してください。",
  parseFailed:
    "この候補はYAMLとして解析できませんでした。選択範囲に改行崩れまたは構文エラーが含まれている可能性があります。Profileへ反映する前に内容を修正してください。",
  selectionParseMixed:
    "この候補は、選択範囲Captureから取得されましたが、YAML構文が壊れているか、複数sectionが混在しているため、自動更新できません。Profileへ反映する前に、内容を修正して再Captureしてください。",
};

const EN = {
  suspiciousMixedSelection:
    "This candidate was rated Suspicious Drift because the selection mixes multiple profile sections. Duplicates or section misclassification are likely.",
  suspiciousMixedPage:
    "This candidate was rated Suspicious Drift because page capture noise may mix multiple kinds of information into a single section. Duplicates or section misclassification are likely.",
  suspiciousConceptsVsProjects:
    "This candidate targets knowledge.concepts but the recommended section is major_projects. Check duplicates before approval.",
  suspiciousDuplicates:
    "Rated Suspicious Drift with overlaps in the profile; direct approval is not recommended.",
  suspiciousGeneric: "Rated Suspicious Drift. Review the diff before approval.",
  critical: "This candidate is Critical Distortion. Reject or create a revised candidate.",
  parseFailed:
    "This candidate could not be parsed as YAML. The capture may contain line breaks or syntax errors. Fix the content before applying to the profile.",
  selectionParseMixed:
    "This candidate was captured from a selection but YAML is broken or mixes multiple sections. Fix the content and re-capture before applying to the profile.",
};

export function buildRdeSummaryFromDiff(
  candidate: CandidateDetail,
  diff: DiffPayload,
  locale: SupportedLocale,
): string {
  const category = candidate.evaluation?.rde_class ?? candidate.rde_class;
  if (!category) return "";

  const messages = locale === "ja" ? JA : EN;
  const meta = captureMeta(candidate);
  const section = String(diff.section ?? candidate.proposal.section ?? "");
  const recommended = String(diff.recommended_section ?? section);
  const operation = String(candidate.proposal.operation ?? "");
  const parseError =
    typeof diff.parse_error === "string"
      ? diff.parse_error
      : candidate.proposal.parse_error;
  const hasDuplicates = Boolean(diff.has_duplicates);
  const updateRecommended = Boolean(diff.profile_update_recommended);
  const mixed = isMixedDiff(diff, candidate);

  if (operation === "parse_failed" || parseError) {
    return messages.parseFailed;
  }

  if (category === "Unresolved Gap") {
    if (section === "review_required" || operation === "parse_failed_or_no_effective_update") {
      const source = captureSourceFromMeta(meta);
      if (source === "selection" || source === "clipboard") {
        return messages.selectionParseMixed;
      }
      return messages.parseFailed;
    }
  }

  if (category === "Suspicious Drift") {
    if (mixed) {
      if (captureSourceFromMeta(meta) === "selection" || captureSourceFromMeta(meta) === "clipboard" || meta.user_selected) {
        return messages.suspiciousMixedSelection;
      }
      if (shouldMentionPageCaptureNoise(meta)) {
        return messages.suspiciousMixedPage;
      }
      return messages.suspiciousMixedSelection;
    }
    if (section === "knowledge.concepts" && recommended === "major_projects") {
      return messages.suspiciousConceptsVsProjects;
    }
    if (hasDuplicates && !updateRecommended) {
      return messages.suspiciousDuplicates;
    }
    return messages.suspiciousGeneric;
  }

  if (category === "Critical Distortion") {
    return messages.critical;
  }

  return "";
}
