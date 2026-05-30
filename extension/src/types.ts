/** Shared extension types. */

export type { InsertTarget } from "./providers/types.js";
import type { InsertTarget } from "./providers/types.js";

export interface ExtensionConfig {
  bridgeUrl: string;
  bridgeToken: string;
  defaultProfileId: string;
  displayLanguage: DisplayLanguage;
}

export type DisplayLanguage = "auto" | "en" | "ja";
export type SupportedLocale = "en" | "ja";

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
  warnings?: string[];
}

export interface CandidateSummary {
  id: string;
  status: string;
  target_profile_id: string;
  source: string;
  source_url: string | null;
  captured_at: string;
  rde_class: string | null;
  evaluation_level: number | null;
  content_preview: string;
}

export interface CandidateDiff {
  add?: unknown[];
  remove?: unknown[];
  modify?: unknown[];
  already_present?: boolean;
  [key: string]: unknown;
}

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
    }
  | { type: "BRIDGE_LIST_CANDIDATES" }
  | { type: "BRIDGE_EVALUATE_CANDIDATE"; candidateId: string; level: number }
  | { type: "BRIDGE_DIFF_CANDIDATE"; candidateId: string }
  | { type: "BRIDGE_APPROVE_CANDIDATE"; candidateId: string; forceCritical?: boolean }
  | { type: "BRIDGE_REJECT_CANDIDATE"; candidateId: string; reason?: string };

export type BackgroundResponse =
  | { ok: true; data?: unknown }
  | { ok: false; error: string };
