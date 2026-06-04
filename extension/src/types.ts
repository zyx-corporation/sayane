/** Shared extension types. */

export type { InsertTarget } from "./providers/types.js";
import type { InsertTarget } from "./providers/types.js";

export interface ExtensionConfig {
  bridgeUrl: string;
  bridgeToken: string;
  defaultProfileId: string;
  displayLanguage: DisplayLanguage;
  developerMode: boolean;
}

export type DisplayLanguage = "auto" | "en" | "ja";
export type SupportedLocale = "en" | "ja";

export interface ProfileSummary {
  id: string;
  path: string;
  name: string | null;
  default_language?: string | null;
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
  status: "pending" | "evaluated" | "approved" | "rejected";
  evaluation_status?: "not_started" | "completed" | "judge_failed";
  evaluation_error?: {
    type: string;
    message: string;
    provider?: string | null;
    status_code?: number | null;
  } | null;
  locale?: string | null;
  target_profile_id: string;
  source: string;
  source_url: string | null;
  captured_at: string;
  rde_class:
    | "Authorized Transformation"
    | "Inferred Extension"
    | "Unresolved Gap"
    | "Suspicious Drift"
    | "Critical Distortion"
    | "Preserved"
    | null;
  evaluation_level: number | null;
  section: string;
  content_preview: string;
}

export interface CandidateDetail extends CandidateSummary {
  content: string;
  proposal: {
    section: string;
    operation?: string;
    parse_error?: string | null;
    add: string[];
    items?: Array<{ name?: string; summary?: string; path?: string; value?: string }>;
    already_present?: Array<{ name?: string; summary?: string; path?: string; value?: string }>;
    summary: string | null;
  };
  evaluation:
    | {
        level: number;
        evaluated_at?: string;
        rde_class:
          | "Authorized Transformation"
          | "Inferred Extension"
          | "Unresolved Gap"
          | "Suspicious Drift"
          | "Critical Distortion"
          | "Preserved";
        notes: Array<
          | string
          | {
              source?: "heuristic" | "llm_judge";
              key?: string | null;
              params?: Record<string, unknown>;
              text?: string | null;
            }
        >;
        uib?: {
          UD: number;
          MI: number;
          CH: number;
          DT: number;
          VP: number;
          FG: number;
        };
        llm_review?: {
          model: string;
          level: number;
          rde_class: string | null;
          notes: Array<string | Record<string, unknown>>;
          uib?: Record<string, number> | null;
        } | null;
      }
    | null;
}

export interface CandidateDiff {
  add?: unknown[];
  remove?: unknown[];
  modify?: unknown[];
  already_present?: unknown[];
  recommended_section?: string;
  has_duplicates?: boolean;
  profile_update_recommended?: boolean;
  [key: string]: unknown;
}

export type SayanePingPayload = {
  ok: true;
  provider: string;
  url: string;
  title: string;
  readable: boolean;
  selectionTextLength: number;
  extractorAvailable: boolean;
  extractorError: string | null;
  hostPermissionOk: boolean;
  contentScriptReady: true;
};

export type PageExtractPayload = {
  raw: string;
  cleaned: string;
  provider: string;
  extractor: string;
  uiNoiseDetected: boolean;
  lowConfidence: boolean;
  extractorError: string | null;
};

export type ContentMessage =
  | { type: "SAYANE_PING" }
  | { type: "EXTRACT_PAGE" }
  | { type: "GET_SELECTION" }
  | { type: "GET_PAGE_SNAPSHOT" }
  | { type: "INSERT_TEXT"; text: string; target: InsertTarget };

export type ContentResponse =
  | SayanePingPayload
  | PageExtractPayload
  | { ok: true; text: string }
  | { ok: true; inserted: true }
  | { ok: false; error: string; code?: string; hint?: string };

export type BackgroundMessage =
  | { type: "BRIDGE_HEALTH" }
  | { type: "BRIDGE_LIST_PROFILES" }
  | {
      type: "BRIDGE_CAPTURE";
      content: string;
      source: string;
      sourceUrl?: string;
      profileId?: string;
      locale?: SupportedLocale;
    }
  | {
      type: "BRIDGE_CONTEXT_PACKET";
      target: InsertTarget;
      profileId: string;
    }
  | { type: "CAPTURE_SELECTION"; tabId: number; profileId?: string; locale?: SupportedLocale }
  | { type: "CAPTURE_PAGE"; tabId: number; profileId?: string; locale?: SupportedLocale }
  | {
      type: "CAPTURE_CLIPBOARD";
      content: string;
      profileId?: string;
      locale?: SupportedLocale;
    }
  | {
      type: "INSERT_CONTEXT_PACKET";
      tabId: number;
      target: InsertTarget;
      profileId: string;
    }
  | { type: "BRIDGE_LIST_CANDIDATES" }
  | { type: "BRIDGE_GET_CANDIDATE"; candidateId: string }
  | { type: "BRIDGE_EVALUATE_CANDIDATE"; candidateId: string; level: number }
  | { type: "BRIDGE_DIFF_CANDIDATE"; candidateId: string }
  | {
      type: "BRIDGE_APPROVE_CANDIDATE";
      candidateId: string;
      forceCritical?: boolean;
      overrideReason?: string;
    }
  | { type: "BRIDGE_REJECT_CANDIDATE"; candidateId: string; reason?: string }
  | { type: "OPEN_SIDE_PANEL"; windowId?: number }
  | { type: "CANDIDATES_CHANGED"; candidateId?: string | null };

export type CandidatesChangedMessage = {
  type: "CANDIDATES_CHANGED";
  candidateId?: string | null;
};

export type BackgroundResponse =
  | { ok: true; data?: unknown }
  | { ok: false; error: string; errorDetails?: Record<string, unknown> };
