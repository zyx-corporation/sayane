/** Shared extension types. */

export type { InsertTarget } from "./providers/types.js";
import type { InsertTarget } from "./providers/types.js";

export interface ExtensionConfig {
  bridgeUrl: string;
  bridgeToken: string;
  defaultProfileId: string;
  displayLanguage: DisplayLanguage;
  developerMode: boolean;
  showDebugUi: boolean;
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

/** Bridge `/preflight/important-terms` — preview only, no Candidate. */
export interface ImportantTermsPreflightSummary {
  section: "important_terms";
  total: number;
  existing_count: number;
  added_count: number;
  removed_count: number;
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
  display_summary?: string | null;
  capture_source?: CaptureSourceKind | string | null;
  proposal_operation?: string | null;
  storage_policy?: CandidateStoragePolicy | null;
  parent_capture_id?: string | null;
}

export type CandidateStoragePolicy = {
  storage_kind: "profile_ir" | "context_note" | "prompt_fragment" | "debug_only";
  target_path: string;
  prompt_export: "default" | "on_demand" | "never";
  sensitivity: "public" | "internal" | "private" | "sensitive";
};

export type CaptureSourceKind = "selection" | "clipboard" | "page";

export interface CaptureMetadataView {
  capture_source?: CaptureSourceKind;
  capture_confidence?: "high" | "low";
  user_selected?: boolean;
  requires_review?: boolean;
  capture_warnings?: string[];
  parse_error?: string | null;
}

export interface CandidateDetail extends CandidateSummary {
  content: string;
  raw_capture?: string | null;
  cleaned_capture?: string | null;
  display_summary?: string | null;
  /** Raw capture input for UI (from Bridge; never Profile IR `content`). */
  source_excerpt?: string | null;
  capture_meta?: CaptureMetadataView | null;
  proposal: {
    section: string;
    operation?: string;
    parse_error?: string | null;
    add: string[];
    items?: Array<{
      name?: string;
      summary?: string;
      path?: string;
      yaml_path?: string;
      section?: string;
      value?: string;
    }>;
    remove?: Array<{ name?: string; path?: string; yaml_path?: string }>;
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

export type LineageOperation =
  | "capture_created"
  | "candidate_generated"
  | "candidate_evaluated"
  | "candidate_diffed"
  | "candidate_approved"
  | "candidate_rejected"
  | "candidate_deferred"
  | "candidate_revised"
  | "context_written"
  | "persona_ir_split";

export interface LineageEvent {
  id: string;
  operation: LineageOperation;
  node_kind: string;
  timestamp: string;
  actor?: string;
  capture_id?: string | null;
  candidate_id?: string | null;
  context_path?: string | null;
  source_kind?: string | null;
  source_url?: string | null;
  note?: string | null;
  metadata?: Record<string, unknown>;
}

export interface CandidateLineage {
  capture_id: string;
  candidate_id: string;
  profile_id: string;
  status: string;
  evaluation_status?: string | null;
  rde_class?: string | null;
  section?: string | null;
  source_kind?: string | null;
  source_url?: string | null;
  captured_at: string;
  decision: "pending" | "approved" | "rejected" | "deferred" | "evaluated";
  context_path?: string | null;
  source_candidate_id?: string | null;
  revised_candidate_id?: string | null;
  operation?: string | null;
  events: LineageEvent[];
}

export interface CandidateDiff {
  add?: unknown[];
  remove?: unknown[];
  modify?: unknown[];
  already_present?: unknown[];
  list_diff?: {
    added?: string[];
    removed?: string[];
    unchanged?: string[];
    unchanged_count?: number;
    operation?: string;
  };
  recommended_section?: string;
  has_duplicates?: boolean;
  profile_update_recommended?: boolean;
  [key: string]: unknown;
}

export interface SummaryCardState {
  key: string;
  value: unknown;
}

export interface QuickLinkState {
  screen: string;
  path: string;
}

export interface AppSurfaceDescriptor {
  path: string;
  purpose: string;
  format?: string;
  method?: string;
  payload_kind?: string;
  result_kind?: string;
}

export interface ScreenStateContractDescriptor {
  screen: string;
  builder: string;
  primary_source: string;
}

export interface SurfaceRoleDescriptor {
  surface: string;
  role: string;
  notes: string[];
}

export interface SharedSemanticDescriptor {
  topic: string;
  shared_by_design: boolean;
  notes: string[];
}

export interface ResidentAppContract {
  kind: "resident_app_contract";
  contract_version: string;
  preferred_entrypoint: string;
  human_surfaces: AppSurfaceDescriptor[];
  read_surfaces: AppSurfaceDescriptor[];
  write_surfaces: AppSurfaceDescriptor[];
  recommended_flow: string[];
  screen_state_contracts: ScreenStateContractDescriptor[];
  surface_roles: SurfaceRoleDescriptor[];
  shared_semantics: SharedSemanticDescriptor[];
  boundaries?: string[];
  non_mvp_boundaries?: Array<Record<string, unknown>>;
}

export interface ResidentAppOverview {
  kind: "resident_app_overview";
  profile_id: string;
  runtime: Record<string, unknown>;
  summary: Record<string, unknown>;
  review_summary: Record<string, unknown>;
  mcp_summary: Record<string, unknown>;
  daemon_summary: Record<string, unknown>;
  review_queue: Record<string, unknown>;
  mcp_preview: Record<string, unknown>;
  daemon_overview: Record<string, unknown>;
}

export interface HomeScreenState {
  kind: "resident_app_home_screen_state";
  summary_cards: SummaryCardState[];
  top_review_items: Array<Record<string, unknown>>;
  top_daemon_actions: Array<Record<string, unknown>>;
  quick_links: QuickLinkState[];
}

export interface CandidateQueueScreenState {
  kind: "resident_app_candidate_queue_screen_state";
  reviewable_count: number;
  status_counts: Record<string, number>;
  top_sections: Array<{ section: string; count: number }>;
  items: CandidateSummary[];
  default_sort: string;
}

export interface CandidateDetailScreenState {
  kind: "resident_app_candidate_detail_screen_state";
  ui_summary: Record<string, unknown>;
  allowed_actions: Record<string, boolean>;
  proposal: Record<string, unknown>;
  evaluation: Record<string, unknown>;
  content?: string;
  diff_available: boolean;
}

export interface DaemonPanelScreenState {
  kind: "resident_app_daemon_panel_screen_state";
  summary_cards: SummaryCardState[];
  next_actions: Array<Record<string, unknown>>;
  runtime_init: Record<string, unknown>;
  cleanup_preview: Record<string, unknown>;
  repair_preview: Record<string, unknown>;
}

export type SayanePingPayload = {
  ok: true;
  provider: string;
  url: string;
  title: string;
  readable: boolean;
  selectionTextLength: number;
  /** Live window.getSelection() length (debug). */
  selectionCurrentLength?: number;
  /** Cached last selection length (debug). */
  selectionCachedLength?: number;
  /** Milliseconds since cache was last updated; null if none (debug). */
  selectionCacheAgeMs?: number | null;
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
  | { type: "BRIDGE_GET_APP_CONTRACT" }
  | { type: "BRIDGE_GET_APP_OVERVIEW" }
  | { type: "BRIDGE_GET_HOME_SCREEN_STATE" }
  | { type: "BRIDGE_GET_CANDIDATE_QUEUE_SCREEN_STATE" }
  | {
      type: "BRIDGE_GET_CANDIDATE_DETAIL_SCREEN_STATE";
      candidateId: string;
    }
  | { type: "BRIDGE_GET_DAEMON_PANEL_SCREEN_STATE" }
  | {
      type: "BRIDGE_PREFLIGHT_IMPORTANT_TERMS";
      content: string;
      profileId?: string;
    }
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
  | {
      type: "CAPTURE_SELECTION";
      tabId: number;
      windowId?: number;
      profileId?: string;
      locale?: SupportedLocale;
    }
  | {
      type: "CAPTURE_PAGE";
      tabId: number;
      windowId?: number;
      profileId?: string;
      locale?: SupportedLocale;
    }
  | {
      type: "CAPTURE_CLIPBOARD";
      content: string;
      windowId?: number;
      profileId?: string;
      locale?: SupportedLocale;
      captureWarnings?: string[];
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
  | { type: "BRIDGE_GET_CANDIDATE_LINEAGE"; candidateId: string }
  | { type: "BRIDGE_GET_CAPTURE_LINEAGE"; captureId: string }
  | {
      type: "BRIDGE_APPROVE_CANDIDATE";
      candidateId: string;
      forceCritical?: boolean;
      overrideReason?: string;
      explicitConfirmation?: {
        section: string;
        checked: true;
        reason: string;
        confirmedAt: string;
      };
    }
  | { type: "BRIDGE_REJECT_CANDIDATE"; candidateId: string; reason?: string }
  | {
      type: "BRIDGE_REVISE_CANDIDATE";
      candidateId: string;
      editedText: string;
      targetSection?: string;
      changeReason?: string;
    }
  | { type: "OPEN_SIDE_PANEL"; windowId?: number }
  | { type: "CANDIDATES_CHANGED"; candidateId?: string | null };

export type CandidatesChangedMessage = {
  type: "CANDIDATES_CHANGED";
  candidateId?: string | null;
};

export type BackgroundResponse =
  | { ok: true; data?: unknown }
  | { ok: false; error: string; errorDetails?: Record<string, unknown> };
