import { loadConfig } from "./config.js";
import type {
  CandidateDetail,
  CandidateDiff,
  CandidateLineage,
  CandidateSummary,
  CaptureResult,
  ContextPacket,
  ImportantTermsPreflightSummary,
  ProfileSummary,
} from "./types.js";

export class BridgeError extends Error {
  constructor(
    message: string,
    readonly status?: number,
    readonly details?: Record<string, unknown>,
  ) {
    super(message);
    this.name = "BridgeError";
  }
}

async function bridgeFetch(path: string, init?: RequestInit): Promise<Response> {
  const config = await loadConfig();
  if (!config.bridgeToken) {
    throw new BridgeError("Bridge token not configured. Set it in Options.");
  }
  const url = `${config.bridgeUrl.replace(/\/$/, "")}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      Authorization: `Bearer ${config.bridgeToken}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    let detail = response.statusText;
    let details: Record<string, unknown> | undefined;
    try {
      const body = (await response.json()) as Record<string, unknown>;
      const nested = body.detail;
      if (nested && typeof nested === "object" && !Array.isArray(nested)) {
        const payload = nested as Record<string, unknown>;
        if (typeof payload.message === "string") {
          detail = payload.message;
          details = payload;
        } else if (typeof payload.error === "string") {
          detail = payload.error;
          details = payload;
        }
      } else if (typeof body.message === "string") {
        detail = body.message;
        details = body;
      } else if (typeof body.detail === "string") {
        detail = body.detail;
      }
    } catch {
      /* ignore */
    }
    throw new BridgeError(detail, response.status, details);
  }
  return response;
}

export async function checkHealthAt(bridgeUrl: string): Promise<boolean> {
  try {
    const res = await fetch(`${bridgeUrl.replace(/\/$/, "")}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function checkHealth(): Promise<boolean> {
  const config = await loadConfig();
  return checkHealthAt(config.bridgeUrl);
}

export type BridgeProbeResult =
  | { ok: true; messageKey: string }
  | { ok: false; messageKey: string; params?: Record<string, string | number> };

/** Options test: /health (no auth) then GET /profiles (requires bearer). */
export async function probeBridge(
  bridgeUrl: string,
  bridgeToken: string,
): Promise<BridgeProbeResult> {
  const base = bridgeUrl.replace(/\/$/, "");
  try {
    const health = await fetch(`${base}/health`);
    if (!health.ok) {
      return { ok: false, messageKey: "options.probe.health_failed" };
    }
  } catch {
    return { ok: false, messageKey: "options.probe.unreachable" };
  }

  const token = bridgeToken.trim();
  if (!token) {
    return { ok: false, messageKey: "options.probe.token_missing" };
  }

  try {
    const res = await fetch(`${base}/profiles`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401 || res.status === 403) {
      return { ok: false, messageKey: "options.probe.unauthorized" };
    }
    if (!res.ok) {
      return { ok: false, messageKey: "options.probe.error", params: { status: res.status } };
    }
    return { ok: true, messageKey: "options.probe.ok" };
  } catch {
    return { ok: false, messageKey: "options.probe.profiles_unreachable" };
  }
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  const res = await bridgeFetch("/profiles");
  return (await res.json()) as ProfileSummary[];
}

export async function preflightImportantTerms(
  content: string,
  profileId = "default",
): Promise<ImportantTermsPreflightSummary> {
  const res = await bridgeFetch("/preflight/important-terms", {
    method: "POST",
    body: JSON.stringify({ content, profile_id: profileId }),
  });
  return (await res.json()) as ImportantTermsPreflightSummary;
}

export type CaptureRequestOptions = {
  rawContent?: string;
  userSelected?: boolean;
  captureSource?: "selection" | "clipboard" | "page";
  captureConfidence?: "high" | "low";
  requiresReview?: boolean;
  captureWarnings?: string[];
  extractor?: string;
};

export async function captureContent(
  content: string,
  source: string,
  sourceUrl?: string,
  profileId = "default",
  locale?: string,
  options: CaptureRequestOptions = {},
): Promise<CaptureResult> {
  const res = await bridgeFetch("/capture", {
    method: "POST",
    body: JSON.stringify({
      content,
      raw_content: options.rawContent,
      source,
      capture_source: options.captureSource,
      source_url: sourceUrl,
      profile_id: profileId,
      locale,
      user_selected: options.userSelected ?? false,
      capture_confidence: options.captureConfidence ?? "high",
      requires_review: options.requiresReview ?? false,
      capture_warnings: options.captureWarnings ?? [],
      extractor: options.extractor,
    }),
  });
  return (await res.json()) as CaptureResult;
}

export async function fetchContextPacket(
  target: string,
  profileId: string,
): Promise<ContextPacket> {
  const params = new URLSearchParams({ target, profile: profileId });
  const res = await bridgeFetch(`/context-packet?${params.toString()}`);
  return (await res.json()) as ContextPacket;
}

export async function listCandidates(): Promise<CandidateSummary[]> {
  const res = await bridgeFetch("/candidates");
  return (await res.json()) as CandidateSummary[];
}

export async function getCandidate(candidateId: string): Promise<CandidateDetail> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}`);
  return (await res.json()) as CandidateDetail;
}

export async function evaluateCandidate(
  candidateId: string,
  level: number,
): Promise<Record<string, unknown>> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}/evaluate`, {
    method: "POST",
    body: JSON.stringify({ level }),
  });
  return (await res.json()) as Record<string, unknown>;
}

export async function diffCandidate(candidateId: string): Promise<CandidateDiff> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}/diff`);
  return (await res.json()) as CandidateDiff;
}

export async function getCandidateLineage(
  candidateId: string,
): Promise<CandidateLineage> {
  const res = await bridgeFetch(
    `/candidates/${encodeURIComponent(candidateId)}/lineage`,
  );
  return (await res.json()) as CandidateLineage;
}

export async function getCaptureLineage(captureId: string): Promise<CandidateLineage> {
  const res = await bridgeFetch(
    `/captures/${encodeURIComponent(captureId)}/lineage`,
  );
  return (await res.json()) as CandidateLineage;
}

export type ExplicitConfirmationPayload = {
  section: string;
  checked: true;
  reason: string;
  confirmed_at: string;
};

export async function approveCandidate(
  candidateId: string,
  forceCritical = false,
  overrideReason?: string,
  explicitConfirmation?: ExplicitConfirmationPayload,
): Promise<Record<string, unknown>> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}/approve`, {
    method: "POST",
    body: JSON.stringify({
      force_critical: forceCritical,
      override_reason: overrideReason ?? null,
      explicit_confirmation: explicitConfirmation ?? null,
    }),
  });
  return (await res.json()) as Record<string, unknown>;
}

export async function rejectCandidate(
  candidateId: string,
  reason?: string,
): Promise<Record<string, unknown>> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason: reason ?? null }),
  });
  return (await res.json()) as Record<string, unknown>;
}

export function formatContextPacketForInsert(packet: ContextPacket): string {
  const { format, payload } = packet;
  if (
    (format === "gemini_working_memo" || format === "deepseek_working_memo")
    && typeof payload.text === "string"
  ) {
    return payload.text;
  }
  if (format === "openai_chat" && Array.isArray(payload.messages)) {
    const messages = payload.messages as Array<{ role: string; content: string }>;
    return messages.map((m) => `[${m.role}]\n${m.content}`).join("\n\n");
  }
  if (format === "anthropic_messages") {
    const system = typeof payload.system === "string" ? payload.system : "";
    const messages = Array.isArray(payload.messages)
      ? (payload.messages as Array<{ role: string; content: string }>)
      : [];
    const user = messages.map((m) => m.content).join("\n\n");
    return `[system]\n${system}\n\n[user]\n${user}`;
  }
  if (format === "gemini_generate_content") {
    const contents = payload.contents as Array<{ parts?: Array<{ text?: string }> }> | undefined;
    const userText = contents?.[0]?.parts?.[0]?.text;
    if (typeof userText === "string") {
      return userText;
    }
  }
  return JSON.stringify(payload, null, 2);
}
