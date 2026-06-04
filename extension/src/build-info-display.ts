/** Format build metadata for Settings / debug UI. */

import { EXTENSION_BUILD_INFO } from "./build-info.js";

export type BuildInfoPayload = {
  version: string;
  sourceUpdatedAt: string;
  component?: string;
};

export function formatSourceUpdatedAt(isoTimestamp: string): string {
  const text = isoTimestamp.trim();
  if (!text) return "—";
  const normalized = text.replace("Z", "+00:00");
  try {
    const dt = new Date(normalized);
    if (Number.isNaN(dt.getTime())) return text.slice(0, 19).replace("T", " ");
    return dt.toLocaleString("en-US", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      timeZoneName: "short",
    });
  } catch {
    return text.slice(0, 19).replace("T", " ");
  }
}

export function extensionBuildInfoLine(): string {
  return `Extension ${EXTENSION_BUILD_INFO.version} · codebase updated ${formatSourceUpdatedAt(
    EXTENSION_BUILD_INFO.sourceUpdatedAt,
  )}`;
}

export function bridgeBuildInfoLine(payload: BuildInfoPayload | null): string {
  if (!payload?.version) {
    return "Bridge — version shown after connection";
  }
  return `Bridge ${payload.version} · codebase updated ${formatSourceUpdatedAt(
    payload.sourceUpdatedAt,
  )}`;
}

export async function fetchBridgeBuildInfo(
  bridgeUrl: string,
): Promise<BuildInfoPayload | null> {
  try {
    const base = bridgeUrl.replace(/\/$/, "");
    const res = await fetch(`${base}/health`);
    if (!res.ok) return null;
    const data = (await res.json()) as Record<string, unknown>;
    const version = typeof data.version === "string" ? data.version : "";
    const sourceUpdatedAt =
      typeof data.source_updated_at === "string" ? data.source_updated_at : "";
    if (!version && !sourceUpdatedAt) return null;
    return {
      version,
      sourceUpdatedAt,
      component: typeof data.component === "string" ? data.component : "sayane",
    };
  } catch {
    return null;
  }
}
