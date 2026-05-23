/** Shared extension types. */

export interface ExtensionConfig {
  bridgeUrl: string;
  bridgeToken: string;
  defaultProfileId: string;
}

export interface ProfileSummary {
  id: string;
  path: string;
  name: string | null;
}

export interface ContextPacket {
  target: string;
  format: string;
  payload: Record<string, unknown>;
  profile_id: string;
}

export interface CaptureResult {
  id: string;
  status: string;
  path: string;
}

export type InsertTarget = "chatgpt" | "claude";

export type ContentMessage =
  | { type: "GET_SELECTION" }
  | { type: "GET_PAGE_SNAPSHOT" }
  | { type: "INSERT_TEXT"; text: string; target: InsertTarget };

export type ContentResponse =
  | { ok: true; text: string }
  | { ok: true; inserted: true }
  | { ok: false; error: string; code?: string; hint?: string };

export type BackgroundMessage =
  | { type: "BRIDGE_HEALTH" }
  | { type: "BRIDGE_LIST_PROFILES" }
  | { type: "BRIDGE_CAPTURE"; content: string; source: string; sourceUrl?: string }
  | {
      type: "BRIDGE_CONTEXT_PACKET";
      target: InsertTarget;
      profileId: string;
    }
  | { type: "CAPTURE_SELECTION"; tabId: number }
  | { type: "CAPTURE_PAGE"; tabId: number }
  | {
      type: "INSERT_CONTEXT_PACKET";
      tabId: number;
      target: InsertTarget;
      profileId: string;
    };

export type BackgroundResponse =
  | { ok: true; data?: unknown }
  | { ok: false; error: string };
