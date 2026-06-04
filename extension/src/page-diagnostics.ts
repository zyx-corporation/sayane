/** Popup page / content-script diagnostics (runtime only — not persisted). */

import type { SayanePingResult } from "./capture/page-extract-core.js";
import { hostProviderFromLocation } from "./capture/page-extract-core.js";
import { getProviderById } from "./providers/registry.js";
import { CONTENT_SCRIPT_BUNDLE } from "./content-script-bundle.js";
import { getActiveCaptureTab, isExtensionPageUrl } from "./tab-target.js";

export type BridgeState =
  | { kind: "unknown" }
  | { kind: "checking" }
  | { kind: "connected" }
  | { kind: "failed"; reason: string };

export type PageState =
  | { kind: "unknown" }
  | { kind: "checking" }
  | { kind: "readable"; ping: SayanePingResult }
  | { kind: "unsupported_url"; url: string; reason: string }
  | { kind: "no_active_tab"; reason: string }
  | { kind: "content_script_unavailable"; url: string; reason: string; lastError?: string }
  | { kind: "extractor_failed"; ping: SayanePingResult; reason: string };

export type CaptureAvailability = {
  bridgeState: BridgeState;
  pageState: PageState;
  tabId: number | null;
  tabUrl: string | null;
  canCaptureSelection: boolean;
  canCaptureClipboard: boolean;
  canCapturePage: boolean;
  selectionDisabledReason: string | null;
  clipboardDisabledReason: string | null;
  pageDisabledReason: string | null;
  debugLines: string[];
};

/** Cumulative delays from first attempt: immediate, +300ms, +800ms. */
const PING_ATTEMPT_DELAYS_MS = [0, 300, 800];

export type PingMessage = { type: "SAYANE_PING" };

export type PingResponse = SayanePingResult | { ok: false; error: string };

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function isPingSuccess(response: PingResponse | null | undefined): response is SayanePingResult {
  return Boolean(response && typeof response === "object" && "contentScriptReady" in response);
}

function hostPermissionForUrl(url: string): boolean {
  try {
    const host = new URL(url).hostname;
    const provider = hostProviderFromLocation(host);
    if (!provider) return false;
    return getProviderById(provider)?.matches(url) ?? false;
  } catch {
    return false;
  }
}

async function injectContentScript(tabId: number): Promise<void> {
  await chrome.scripting.executeScript({
    target: { tabId },
    files: [CONTENT_SCRIPT_BUNDLE],
  });
}

async function pingAttempts(trySend: () => Promise<PingResponse>): Promise<PingResponse> {
  let last: PingResponse = { ok: false, error: "no response" };
  for (let i = 0; i < PING_ATTEMPT_DELAYS_MS.length; i++) {
    if (i > 0) {
      await sleep(PING_ATTEMPT_DELAYS_MS[i] - PING_ATTEMPT_DELAYS_MS[i - 1]);
    }
    last = await trySend();
    if (isPingSuccess(last)) return last;
  }
  return last;
}

export async function pingTab(tabId: number, tabUrl: string): Promise<PingResponse> {
  const hostOk = hostPermissionForUrl(tabUrl);
  const message: PingMessage = { type: "SAYANE_PING" };

  const trySend = (): Promise<PingResponse> =>
    new Promise((resolve) => {
      chrome.tabs.sendMessage(tabId, message, (response) => {
        const err = chrome.runtime.lastError;
        if (err) {
          resolve({ ok: false, error: err.message ?? "no response" });
          return;
        }
        if (!response || typeof response !== "object") {
          resolve({ ok: false, error: "empty response" });
          return;
        }
        resolve(response as PingResponse);
      });
    });

  let response = await pingAttempts(trySend);
  if (!isPingSuccess(response)) {
    try {
      await injectContentScript(tabId);
      response = await pingAttempts(trySend);
    } catch (injectErr) {
      return { ok: false, error: String(injectErr) };
    }
  }

  if (isPingSuccess(response)) {
    return { ...response, hostPermissionOk: hostOk };
  }
  return response.ok === false ? response : { ok: false, error: "empty response" };
}

export function deriveCaptureAvailability(
  bridgeState: BridgeState,
  pageState: PageState,
  tabId: number | null,
  tabUrl: string | null,
  t: (key: string, params?: Record<string, string | number>) => string,
): CaptureAvailability {
  const debugLines: string[] = [];
  const bridgeConnected = bridgeState.kind === "connected";

  debugLines.push(`${t("debug.bridge")}: ${bridgeState.kind}`);
  if (tabUrl) debugLines.push(`${t("debug.url")}: ${tabUrl}`);

  let canCaptureSelection = false;
  let canCaptureClipboard = false;
  let canCapturePage = false;
  let selectionDisabledReason: string | null = null;
  let clipboardDisabledReason: string | null = null;
  let pageDisabledReason: string | null = null;

  if (!bridgeConnected) {
    const reason =
      bridgeState.kind === "failed"
        ? bridgeState.reason
        : t("page.reason.bridge_not_connected");
    selectionDisabledReason = reason;
    clipboardDisabledReason = reason;
    pageDisabledReason = reason;
    debugLines.push(`${t("debug.selection")}: false (${reason})`);
    debugLines.push(`${t("debug.clipboard")}: false (${reason})`);
    debugLines.push(`${t("debug.page_capture")}: false (${reason})`);
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  canCaptureClipboard = true;
  clipboardDisabledReason = null;
  debugLines.push(`${t("debug.clipboard")}: true`);

  if (pageState.kind === "checking" || pageState.kind === "unknown") {
    selectionDisabledReason = t("page.reason.checking");
    pageDisabledReason = t("page.reason.checking");
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  if (pageState.kind === "no_active_tab") {
    selectionDisabledReason = pageState.reason;
    pageDisabledReason = pageState.reason;
    debugLines.push(`${t("debug.content_script")}: n/a`);
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  if (pageState.kind === "unsupported_url") {
    selectionDisabledReason = pageState.reason;
    pageDisabledReason = pageState.reason;
    debugLines.push(`${t("debug.provider")}: ${t("page.unsupported")}`);
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  if (pageState.kind === "content_script_unavailable") {
    const reason = pageState.reason;
    selectionDisabledReason = reason;
    pageDisabledReason = reason;
    debugLines.push(`${t("debug.content_script")}: ${t("debug.no_response")}`);
    debugLines.push(`${t("debug.page_readable")}: false`);
    debugLines.push(`${t("debug.selection_length")}: 0`);
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  const ping =
    pageState.kind === "readable" || pageState.kind === "extractor_failed"
      ? pageState.ping
      : null;

  if (!ping) {
    selectionDisabledReason = t("page.reason.unknown");
    pageDisabledReason = t("page.reason.unknown");
    return {
      bridgeState,
      pageState,
      tabId,
      tabUrl,
      canCaptureSelection,
      canCaptureClipboard,
      canCapturePage,
      selectionDisabledReason,
      clipboardDisabledReason,
      pageDisabledReason,
      debugLines,
    };
  }

  debugLines.push(`${t("debug.provider")}: ${ping.provider}`);
  debugLines.push(
    `${t("debug.content_script")}: ${ping.contentScriptReady ? t("debug.ok") : t("debug.no_response")}`,
  );
  debugLines.push(`${t("debug.page_readable")}: ${ping.readable}`);
  debugLines.push(`${t("debug.selection_length")}: ${ping.selectionTextLength}`);
  if (typeof ping.selectionCurrentLength === "number") {
    debugLines.push(
      `${t("debug.selection_current_length")}: ${ping.selectionCurrentLength}`,
    );
  }
  if (typeof ping.selectionCachedLength === "number") {
    debugLines.push(
      `${t("debug.selection_cached_length")}: ${ping.selectionCachedLength}`,
    );
  }
  if (ping.selectionCacheAgeMs != null) {
    debugLines.push(
      `${t("debug.selection_cache_age_ms")}: ${ping.selectionCacheAgeMs}`,
    );
  }
  debugLines.push(
    `${t("debug.extractor")}: ${ping.extractorAvailable ? t("debug.ok") : t("debug.failed")}`,
  );
  debugLines.push(
    `${t("debug.host_permission")}: ${ping.hostPermissionOk ? t("debug.ok") : t("debug.failed")}`,
  );

  const selectionOk = ping.contentScriptReady && ping.selectionTextLength > 0;
  canCaptureSelection = selectionOk;
  if (!selectionOk) {
    selectionDisabledReason =
      ping.selectionTextLength > 0
        ? t("page.reason.content_script_unavailable")
        : t("page.reason.no_selection");
  }

  const pageOk =
    ping.contentScriptReady && ping.extractorAvailable && ping.readable && ping.hostPermissionOk;
  canCapturePage = pageOk;
  if (!pageOk) {
    if (!ping.hostPermissionOk) {
      pageDisabledReason = t("page.reason.host_permission");
    } else if (!ping.extractorAvailable) {
      pageDisabledReason = t("page.reason.extractor_failed", {
        provider: ping.provider,
      });
    } else if (!ping.readable) {
      pageDisabledReason = t("page.reason.not_readable");
    } else {
      pageDisabledReason = t("page.reason.content_script_unavailable");
    }
  }

  if (pageState.kind === "extractor_failed") {
    pageDisabledReason = pageState.reason;
    canCapturePage = false;
  }

  debugLines.push(`${t("debug.selection")}: ${canCaptureSelection}`);
  debugLines.push(`${t("debug.page_capture")}: ${canCapturePage}`);

  return {
    bridgeState,
    pageState,
    tabId,
    tabUrl,
    canCaptureSelection,
    canCaptureClipboard,
    canCapturePage,
    selectionDisabledReason,
    clipboardDisabledReason,
    pageDisabledReason,
    debugLines,
  };
}

export async function diagnoseActiveTab(
  t: (key: string, params?: Record<string, string | number>) => string,
): Promise<{ pageState: PageState; tabId: number | null; tabUrl: string | null }> {
  const tab = await getActiveCaptureTab();
  if (!tab?.id) {
    const [anyTab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (anyTab?.url && isExtensionPageUrl(anyTab.url)) {
      return {
        pageState: {
          kind: "unsupported_url",
          url: anyTab.url,
          reason: t("page.reason.extension_page_active"),
        },
        tabId: null,
        tabUrl: anyTab.url ?? null,
      };
    }
    return {
      pageState: { kind: "no_active_tab", reason: t("error.no_active_tab") },
      tabId: null,
      tabUrl: null,
    };
  }

  const tabUrl = tab.url ?? "";
  if (isExtensionPageUrl(tabUrl)) {
    return {
      pageState: {
        kind: "unsupported_url",
        url: tabUrl,
        reason: t("page.reason.extension_page_active"),
      },
      tabId: null,
      tabUrl,
    };
  }

  if (!hostPermissionForUrl(tabUrl)) {
    return {
      pageState: {
        kind: "unsupported_url",
        url: tabUrl,
        reason: t("page.reason.host_permission"),
      },
      tabId: tab.id,
      tabUrl,
    };
  }

  const ping = await pingTab(tab.id, tabUrl);
  if (!isPingSuccess(ping)) {
    return {
      pageState: {
        kind: "content_script_unavailable",
        url: tabUrl,
        reason: t("page.reason.content_script_unavailable"),
        lastError: ping.error,
      },
      tabId: tab.id,
      tabUrl,
    };
  }

  if (!ping.extractorAvailable || !ping.readable) {
    return {
      pageState: {
        kind: "extractor_failed",
        ping,
        reason: t("page.reason.extractor_failed", { provider: ping.provider }),
      },
      tabId: tab.id,
      tabUrl,
    };
  }

  return {
    pageState: { kind: "readable", ping },
    tabId: tab.id,
    tabUrl,
  };
}
