import type { CandidateSummary, ProfileSummary, SupportedLocale } from "./types.js";
import { normalizeLocale } from "./i18n.js";

export type CandidateStatus = CandidateSummary["status"];
export type CandidateCategory = NonNullable<CandidateSummary["rde_class"]>;

export const STATUS_LABELS: Record<SupportedLocale, Record<CandidateStatus, string>> = {
  ja: {
    pending: "未評価",
    evaluated: "評価済み",
    approved: "採用済み",
    rejected: "棄却済み",
  },
  en: {
    pending: "pending",
    evaluated: "evaluated",
    approved: "approved",
    rejected: "rejected",
  },
};

export const RDE_CATEGORY_LABELS: Record<SupportedLocale, Record<CandidateCategory, string>> = {
  ja: {
    Preserved: "保存された要素",
    "Authorized Transformation": "許可された変換",
    "Inferred Extension": "推論による補完",
    "Unresolved Gap": "未解決の差分",
    "Suspicious Drift": "疑わしい逸脱",
    "Critical Distortion": "重大な歪曲",
  },
  en: {
    Preserved: "Preserved",
    "Authorized Transformation": "Authorized Transformation",
    "Inferred Extension": "Inferred Extension",
    "Unresolved Gap": "Unresolved Gap",
    "Suspicious Drift": "Suspicious Drift",
    "Critical Distortion": "Critical Distortion",
  },
};

export const UNSAFE_APPROVE_CATEGORIES = new Set<CandidateCategory>([
  "Preserved",
  "Unresolved Gap",
  "Suspicious Drift",
  "Critical Distortion",
]);

const RDE_CSS: Record<CandidateCategory, string> = {
  Preserved: "rde-preserved",
  "Authorized Transformation": "rde-authorized",
  "Inferred Extension": "rde-inferred",
  "Unresolved Gap": "rde-unresolved",
  "Suspicious Drift": "rde-suspicious",
  "Critical Distortion": "rde-critical",
};

const RDE_SEVERITY: Record<CandidateCategory, number> = {
  Preserved: 0,
  "Inferred Extension": 1,
  "Unresolved Gap": 2,
  "Authorized Transformation": 3,
  "Suspicious Drift": 4,
  "Critical Distortion": 5,
};

const STATUS_CSS: Record<CandidateStatus, string> = {
  pending: "status-pending",
  evaluated: "status-evaluated",
  approved: "status-approved",
  rejected: "status-rejected",
};

export function isKnownRdeCategory(value: string): value is CandidateCategory {
  return value in RDE_CATEGORY_LABELS.en;
}

export function rdeCssClass(category: string | null | undefined): string {
  if (!category || !isKnownRdeCategory(category)) return "rde-unknown";
  return RDE_CSS[category];
}

export function rdeSeverity(category: string | null | undefined): number {
  if (!category || !isKnownRdeCategory(category)) return -1;
  return RDE_SEVERITY[category];
}

export function statusCssClass(status: string): string {
  if (status in STATUS_CSS) return STATUS_CSS[status as CandidateStatus];
  return "status-unknown";
}

export function canApproveWithCriticalOverride(
  status: CandidateStatus,
  category: CandidateCategory | null,
): boolean {
  if (status !== "evaluated") return false;
  if (!category) return true;
  if (category === "Critical Distortion") return true;
  return canApprove(status, category);
}

export function resolveCandidateLocale(
  candidate: CandidateSummary | null,
  selectedProfile: ProfileSummary | null,
  uiLocale: SupportedLocale,
): SupportedLocale {
  if (candidate?.locale) return normalizeLocale(candidate.locale);
  if (selectedProfile?.default_language) {
    return normalizeLocale(selectedProfile.default_language);
  }
  return uiLocale || "en";
}

export function statusLabel(status: CandidateStatus, locale: SupportedLocale): string {
  return STATUS_LABELS[locale][status] ?? status;
}

export function statusWithJudgeLabel(
  status: CandidateStatus,
  evaluationStatus: CandidateSummary["evaluation_status"] | undefined,
  locale: SupportedLocale,
): string {
  const base = statusLabel(status, locale);
  if (evaluationStatus === "judge_failed") {
    return locale === "ja" ? `${base} · LLM評価失敗` : `${base} · judge failed`;
  }
  return base;
}

export function categoryLabel(category: CandidateCategory, locale: SupportedLocale): string {
  return RDE_CATEGORY_LABELS[locale][category] ?? category;
}

export function canEvaluate(status: CandidateStatus): boolean {
  return status !== "approved" && status !== "rejected";
}

export function canReject(status: CandidateStatus): boolean {
  return status !== "approved" && status !== "rejected";
}

export function canApprove(status: CandidateStatus, category: CandidateCategory | null): boolean {
  if (status !== "evaluated") return false;
  if (!category) return true;
  return !UNSAFE_APPROVE_CATEGORIES.has(category);
}
