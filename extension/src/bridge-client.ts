import { loadConfig } from "./config.js";
import type {
  CandidateDiff,
  CandidateSummary,
  CaptureResult,
  ContextPacket,
  ProfileSummary,
} from "./types.js";

export class BridgeError extends Error {
  constructor(
    message: string,
    readonly status?: number,
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
    try {
      const body = (await response.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      /* ignore */
    }
    throw new BridgeError(detail, response.status);
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

export type BridgeProbeResult = { ok: true; message: string } | { ok: false; message: string };

/** Options test: /health (no auth) then GET /profiles (requires bearer). */
export async function probeBridge(
  bridgeUrl: string,
  bridgeToken: string,
): Promise<BridgeProbeResult> {
  const base = bridgeUrl.replace(/\/$/, "");
  try {
    const health = await fetch(`${base}/health`);
    if (!health.ok) {
      return { ok: false, message: "Bridge unreachable (/health failed)" };
    }
  } catch {
    return { ok: false, message: "Bridge unreachable" };
  }

  const token = bridgeToken.trim();
  if (!token) {
    return { ok: false, message: "Bearer token not configured" };
  }

  try {
    const res = await fetch(`${base}/profiles`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.status === 401 || res.status === 403) {
      return { ok: false, message: "Invalid bearer token (unauthorized)" };
    }
    if (!res.ok) {
      return { ok: false, message: `Bridge error (${res.status})` };
    }
    return { ok: true, message: "Bridge OK (/health + /profiles)" };
  } catch {
    return { ok: false, message: "Bridge unreachable (/profiles)" };
  }
}

export async function listProfiles(): Promise<ProfileSummary[]> {
  const res = await bridgeFetch("/profiles");
  return (await res.json()) as ProfileSummary[];
}

export async function captureContent(
  content: string,
  source: string,
  sourceUrl?: string,
): Promise<CaptureResult> {
  const res = await bridgeFetch("/capture", {
    method: "POST",
    body: JSON.stringify({ content, source, source_url: sourceUrl }),
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

export async function approveCandidate(
  candidateId: string,
  forceCritical = false,
): Promise<Record<string, unknown>> {
  const res = await bridgeFetch(`/candidates/${encodeURIComponent(candidateId)}/approve`, {
    method: "POST",
    body: JSON.stringify({ force_critical: forceCritical }),
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
  return JSON.stringify(payload, null, 2);
}
