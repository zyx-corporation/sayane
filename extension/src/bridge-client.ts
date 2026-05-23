import { loadConfig } from "./config.js";
import type { CaptureResult, ContextPacket, ProfileSummary } from "./types.js";

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

export async function checkHealth(): Promise<boolean> {
  const config = await loadConfig();
  try {
    const res = await fetch(`${config.bridgeUrl.replace(/\/$/, "")}/health`);
    return res.ok;
  } catch {
    return false;
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
