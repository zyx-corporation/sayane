import {
  approveCandidate,
  BridgeError,
  diffCandidate,
  evaluateCandidate,
  getCandidate,
  listProfiles,
  rejectCandidate,
} from "./bridge-client.js";
import {
  canApprove,
  canEvaluate,
  canReject,
  categoryLabel,
  resolveCandidateLocale,
  statusWithJudgeLabel,
} from "./candidate-display.js";
import { buildRdeSummaryFromDiff } from "./diff-summary.js";
import { formatEvaluationNotes } from "./rde-notes.js";
import { BusyUiController } from "./busy-ui.js";
import { applyDataI18n, getLocale, initI18n, localizeError, t } from "./i18n.js";
import type { CandidateDetail, CandidateSummary, ProfileSummary, SupportedLocale } from "./types.js";

function $(id: string): HTMLElement {
  const el = document.getElementById(id);
  if (!el) throw new Error(`Missing #${id}`);
  return el;
}

function setStatus(text: string, isError = false): void {
  const el = $("status");
  el.textContent = text;
  el.className = isError ? "status error" : "status";
}

const busyUi = new BusyUiController($("app-root"));

function registerBusyButtons(): void {
  busyUi.registerButton("btn-evaluate", $("btn-evaluate") as HTMLButtonElement, {
    busyKey: "evaluating",
    idleLabel: t("candidate.evaluate"),
    busyLabel: t("busy.evaluating"),
  });
  busyUi.registerButton("btn-approve", $("btn-approve") as HTMLButtonElement, {
    busyKey: "approving",
    idleLabel: t("candidate.approve"),
    busyLabel: t("busy.approving"),
    blockDuringCandidateMutation: true,
  });
  busyUi.registerButton("btn-reject", $("btn-reject") as HTMLButtonElement, {
    busyKey: "rejecting",
    idleLabel: t("candidate.reject"),
    busyLabel: t("busy.rejecting"),
    blockDuringCandidateMutation: true,
  });
}

function setDiffContentLoading(loading: boolean): void {
  const diffEl = $("content-diff");
  if (loading) {
    diffEl.textContent = t("diff.status.loading");
    diffEl.classList.add("content-loading");
    return;
  }
  diffEl.classList.remove("content-loading");
}

function formatDateTime(value: unknown, locale: string): string {
  if (!value || typeof value !== "string") {
    return locale.startsWith("ja") ? "不明" : "unknown";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return locale.startsWith("ja") ? "不明" : "unknown";
  }
  return new Intl.DateTimeFormat(locale, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

function candidateCreatedAt(candidate: CandidateDetail, locale: string): string {
  const unknownText = locale.startsWith("ja") ? "不明" : "unknown";
  const candidateRecord = candidate as unknown as Record<string, unknown>;
  const values = [
    candidateRecord.created_at,
    candidate.captured_at,
    candidateRecord.updated_at,
    candidate.evaluation?.evaluated_at,
  ];
  for (const value of values) {
    const formatted = formatDateTime(value, locale);
    if (formatted !== unknownText) return formatted;
  }
  return unknownText;
}

function formatBridgeError(error: unknown): string {
  if (error instanceof BridgeError) {
    const details = error.details;
    if (details && typeof details.message === "string") {
      return localizeError(details.message);
    }
    return localizeError(error.message);
  }
  return localizeError(String(error));
}

function candidateIdFromQuery(): string | null {
  const params = new URLSearchParams(location.search);
  return params.get("candidateId");
}

let currentCandidate: CandidateDetail | null = null;
let profilesById = new Map<string, ProfileSummary>();

function selectedLocale(candidate: CandidateDetail): SupportedLocale {
  return resolveCandidateLocale(
    candidate as CandidateSummary,
    profilesById.get(candidate.target_profile_id) ?? null,
    getLocale(),
  );
}

function actionHint(
  candidate: CandidateDetail,
  diff: Record<string, unknown>,
  locale: SupportedLocale,
): string {
  return buildRdeSummaryFromDiff(candidate, diff, locale);
}

function judgeFailureHint(candidate: CandidateDetail, locale: SupportedLocale): string {
  if (candidate.evaluation_status !== "judge_failed") return "";
  const statusCode = candidate.evaluation_error?.status_code;
  if (locale === "ja") {
    const firstLine =
      statusCode === 401
        ? "LLM評価に失敗しました。評価用LLMのAPIキーが未設定、無効、または権限不足の可能性があります。"
        : statusCode === 429
          ? "LLM評価に失敗しました。評価用LLMでレート制限またはクォータ超過が発生している可能性があります。"
          : "LLM評価に失敗しました。評価用LLMの設定または接続を確認してください。";
    return (
      `${firstLine}\n` +
      "Captureされた内容はCandidateとして保存されていますが、LLM judgeによる評価は完了していません。"
    );
  }
  return (
    "LLM judge failed. The API key for the configured judge provider may be missing, invalid, or unauthorized.\n"
    + "The captured content was saved as a Candidate, but LLM-based evaluation was not completed."
  );
}

function updateButtons(candidate: CandidateDetail): void {
  const category = candidate.evaluation?.rde_class ?? null;
  const mutationBusy = busyUi.shouldDisableCandidateActions();
  const approveBtn = $("btn-approve") as HTMLButtonElement;

  busyUi.applyExternalDisabled("btn-evaluate", mutationBusy || !canEvaluate(candidate.status));
  busyUi.applyExternalDisabled("btn-reject", mutationBusy || !canReject(candidate.status));
  busyUi.applyExternalDisabled(
    "btn-approve",
    mutationBusy || !canApprove(candidate.status, category),
  );

  if (approveBtn.disabled && category === "Suspicious Drift") {
    approveBtn.title = "疑わしい逸脱と評価されているため、そのまま採用できません。";
  } else if (approveBtn.disabled && category === "Preserved") {
    approveBtn.title = "変更がないため採用は不要です。";
  } else {
    approveBtn.title = "";
  }
}

function formatSectionLabel(section: string, locale: SupportedLocale): string {
  if (section === "mixed_sections") {
    return locale === "ja" ? "複数sectionが混在" : "mixed sections";
  }
  if (section === "review_required") {
    return locale === "ja" ? "要確認" : "review required";
  }
  if (section === "organization.name") {
    return locale === "ja" ? "organization.name" : "organization.name";
  }
  if (section === "knowledge.concepts") {
    return locale === "ja" ? "core_concepts / knowledge.concepts" : "core_concepts / knowledge.concepts";
  }
  if (section === "canonical_terms") {
    return locale === "ja" ? "canonical_terms（正規語彙）" : "canonical_terms";
  }
  return section;
}

function captureQualityHint(candidate: CandidateDetail, locale: SupportedLocale): string {
  const meta = (candidate as CandidateDetail & { capture_meta?: { capture_warnings?: string[] } })
    .capture_meta;
  const warnings = meta?.capture_warnings ?? [];
  if (!warnings.length) return "";
  if (warnings.includes("page_capture_low_confidence") || warnings.includes("ui_noise_detected")) {
    return locale === "ja"
      ? "注意: ページ全体Capture由来のため、UIノイズが含まれている可能性があります。"
      : "Note: Page capture may include UI navigation noise.";
  }
  return "";
}

function itemSectionLines(candidate: CandidateDetail, locale: SupportedLocale): string[] {
  const lines: string[] = [];
  for (const item of candidate.proposal.items ?? []) {
    const row = item as { section?: string; name?: string; path?: string };
    const label = formatSectionLabel(String(row.section ?? "-"), locale);
    const name = row.name ?? row.path ?? "";
    if (name) lines.push(`  - ${name} → ${label}`);
  }
  for (const entry of candidate.proposal.already_present ?? []) {
    const row = entry as { name?: string; path?: string };
    const name = row.name ?? "";
    const path = row.path ?? "";
    if (name && path) lines.push(`  - ${name}（既存: ${path}）`);
  }
  return lines;
}

function projectSectionSummary(
  candidate: CandidateDetail,
  diff: Record<string, unknown>,
  locale: SupportedLocale,
): string {
  const proposalSection = formatSectionLabel(
    String(diff.section ?? (candidate.proposal.section || "-")),
    locale,
  );
  const recommended = formatSectionLabel(
    String(diff.recommended_section ?? (candidate.proposal.section || "-")),
    locale,
  );
  const duplicates = Boolean(diff.has_duplicates);
  const updateRecommended = Boolean(diff.profile_update_recommended);
  const itemLines = itemSectionLines(candidate, locale);
  const header =
    locale === "ja"
      ? [
          `diff.section: ${proposalSection}`,
          `diff.recommended_section: ${recommended}`,
          `既存項目との重複: ${duplicates ? "あり" : "なし"}`,
          `profile_update_recommended: ${updateRecommended ? "true" : "false"}`,
        ]
      : [
          `diff.section: ${proposalSection}`,
          `diff.recommended_section: ${recommended}`,
          `Duplicates: ${duplicates ? "yes" : "no"}`,
          `profile_update_recommended: ${updateRecommended ? "true" : "false"}`,
        ];
  if (itemLines.length === 0) return header.join("\n");
  const itemsHeading = locale === "ja" ? "項目ごとの推定section:" : "Per-item inferred sections:";
  return [...header, itemsHeading, ...itemLines].join("\n");
}

function renderCandidate(candidate: CandidateDetail, diff: Record<string, unknown>): void {
  const locale = selectedLocale(candidate);
  const profile = profilesById.get(candidate.target_profile_id);
  const status = statusWithJudgeLabel(
    candidate.status,
    candidate.evaluation_status,
    locale,
  );
  const categoryRaw = candidate.evaluation?.rde_class ?? candidate.rde_class;
  const category = categoryRaw ? categoryLabel(categoryRaw, locale) : "-";
  const localeLabel = locale === "ja" ? "日本語" : "English";
  const localeCode = locale === "ja" ? "ja-JP" : "en-US";
  const captured = candidateCreatedAt(candidate, localeCode);
  const profileText = profile?.name ? `${candidate.target_profile_id} — ${profile.name}` : candidate.target_profile_id;
  const storedLevel = candidate.evaluation?.level ?? "-";
  const reevaluateLevel = Number(($("eval-level") as HTMLSelectElement).value) || 1;

  $("meta").textContent =
    `${t("diff.meta.id")}: ${candidate.id}\n` +
    `${t("diff.meta.status")}: ${status}\n` +
    `${t("diff.meta.category")}: ${category}\n` +
    `${t("diff.meta.locale")}: ${localeLabel}\n` +
    `${t("diff.meta.level")}: ${storedLevel}\n` +
    `${t("diff.meta.relevel")}: ${reevaluateLevel}\n` +
    `${t("diff.meta.captured_at")}: ${captured}\n` +
    `${t("diff.meta.profile")}: ${profileText}`;

  const apiSummary =
    typeof diff.rde_summary_message === "string" ? diff.rde_summary_message.trim() : "";
  const warning = apiSummary || actionHint(candidate, diff, locale);
  const judgeHint = judgeFailureHint(candidate, locale);
  const captureHint = captureQualityHint(candidate, locale);
  const sectionSummary = projectSectionSummary(candidate, diff, locale);
  const warningEl = $("warning");
  warningEl.textContent = [captureHint, warning, sectionSummary, judgeHint]
    .filter(Boolean)
    .join("\n\n");
  warningEl.hidden =
    !captureHint && warning.length === 0 && judgeHint.length === 0 && sectionSummary.length === 0;

  const rawCapture = (candidate as CandidateDetail & { raw_capture?: string | null }).raw_capture;
  const cleaned = (candidate as CandidateDetail & { cleaned_capture?: string | null })
    .cleaned_capture;
  $("content-source").textContent = rawCapture || cleaned || candidate.content;
  const rawEl = $("content-raw");
  if (rawCapture && rawCapture !== (cleaned || candidate.content)) {
    rawEl.textContent = rawCapture;
    (rawEl.parentElement as HTMLDetailsElement).open = false;
    (rawEl.parentElement as HTMLDetailsElement).hidden = false;
  } else {
    rawEl.textContent = "";
    (rawEl.parentElement as HTMLDetailsElement).hidden = true;
  }
  $("content-proposal").textContent = JSON.stringify(candidate.proposal, null, 2);
  $("content-diff").textContent = JSON.stringify(diff, null, 2);
  $("content-rde").textContent = JSON.stringify(candidate.evaluation ?? {}, null, 2);
  $("content-notes").textContent = formatEvaluationNotes(
    (candidate.evaluation?.notes ?? []) as Parameters<typeof formatEvaluationNotes>[0],
    locale,
  );

  updateButtons(candidate);
}

async function refresh(): Promise<void> {
  const cid = candidateIdFromQuery();
  if (!cid) {
    setStatus(t("diff.error.missing_id"), true);
    return;
  }
  await busyUi.run("loadingDiff", async () => {
    setDiffContentLoading(true);
    setStatus(t("diff.status.loading"));
    try {
      const [candidate, diff] = await Promise.all([getCandidate(cid), diffCandidate(cid)]);
      currentCandidate = candidate;
      setDiffContentLoading(false);
      renderCandidate(candidate, diff as Record<string, unknown>);
      setStatus(t("diff.status.loaded", { id: cid.slice(0, 8) }));
    } catch (error) {
      setDiffContentLoading(false);
      $("content-diff").textContent = "";
      setStatus(`${t("diff.error.fetch_failed")} ${formatBridgeError(error)}`, true);
    }
  });
}

async function runAction(action: "evaluate" | "approve" | "reject"): Promise<void> {
  if (!currentCandidate) return;
  const busyKey = action === "evaluate" ? "evaluating" : action === "approve" ? "approving" : "rejecting";
  await busyUi.run(busyKey, async () => {
    try {
      if (action === "evaluate") {
        const level = Number(($("eval-level") as HTMLSelectElement).value) || 1;
        await evaluateCandidate(currentCandidate!.id, level);
        setStatus(t("status.evaluated", { summary: currentCandidate!.id.slice(0, 8) }));
      } else if (action === "approve") {
        await approveCandidate(currentCandidate!.id);
        setStatus(t("status.approved", { id: currentCandidate!.id.slice(0, 8) }));
      } else {
        await rejectCandidate(currentCandidate!.id, "rejected from diff window");
        setStatus(t("status.rejected", { id: currentCandidate!.id.slice(0, 8) }));
      }
      await refresh();
    } catch (error) {
      setStatus(formatBridgeError(error), true);
      if (currentCandidate) updateButtons(currentCandidate);
    }
  });
}

async function init(): Promise<void> {
  await initI18n();
  applyDataI18n(document);
  document.title = t("diff.title");
  const profiles = await listProfiles();
  profilesById = new Map(profiles.map((p) => [p.id, p]));

  $("title").textContent = t("diff.title");
  $("heading-meta").textContent = t("diff.section.meta");
  $("heading-source").textContent = t("diff.section.source");
  $("heading-proposal").textContent = t("diff.section.proposal");
  $("heading-diff").textContent = t("diff.section.diff");
  $("heading-rde").textContent = t("diff.section.rde");
  $("heading-notes").textContent = t("diff.section.notes");
  const rawHeading = document.getElementById("heading-raw");
  if (rawHeading) {
    rawHeading.textContent = t("diff.section.raw");
  }
  const evalSelect = $("eval-level") as HTMLSelectElement;
  const option1 = evalSelect.options.item(0);
  const option2 = evalSelect.options.item(1);
  const option3 = evalSelect.options.item(2);
  if (option1) option1.textContent = `${t("diff.meta.relevel")} 1`;
  if (option2) option2.textContent = `${t("diff.meta.relevel")} 2`;
  if (option3) option3.textContent = `${t("diff.meta.relevel")} 3`;
  ($("btn-close") as HTMLButtonElement).textContent = t("diff.close");

  registerBusyButtons();
  busyUi.setOnStateChange(() => {
    if (currentCandidate) updateButtons(currentCandidate);
  });

  $("btn-evaluate").addEventListener("click", () => void runAction("evaluate"));
  $("btn-approve").addEventListener("click", () => void runAction("approve"));
  $("btn-reject").addEventListener("click", () => void runAction("reject"));
  $("btn-close").addEventListener("click", () => window.close());

  await refresh();
}

void init();
