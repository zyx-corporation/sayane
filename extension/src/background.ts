/**
 * Service worker — Bridge API calls (token stays here, not in content scripts).
 */

import {
  BridgeError,
  approveCandidate,
  captureContent,
  checkHealth,
  diffCandidate,
  evaluateCandidate,
  fetchContextPacket,
  formatContextPacketForInsert,
  getCandidate,
  listCandidates,
  listProfiles,
  rejectCandidate,
} from "./bridge-client.js";
import {
  insertTextInTab,
  readPageFromTab,
  readSelectionFromTab,
} from "./content-script-client.js";
import { afterCaptureNotifyReview } from "./sidepanel-client.js";
import type { ReviewCaptureSource } from "./review-session.js";
import type { BackgroundMessage, BackgroundResponse } from "./types.js";
import type { CaptureResult } from "./types.js";

async function finishCaptureFlow(
  windowId: number | undefined,
  captured: CaptureResult,
  meta: { source: ReviewCaptureSource; profileId: string; rawCaptureText?: string },
): Promise<void> {
  if (windowId == null) {
    return;
  }
  await afterCaptureNotifyReview(windowId, {
    captureId: captured.id,
    source: meta.source,
    profileId: meta.profileId,
    candidateIds: [captured.id],
    rawCaptureText: meta.rawCaptureText ?? "",
  });
}

chrome.runtime.onMessage.addListener(
  (
    message: BackgroundMessage,
    _sender,
    sendResponse: (response: BackgroundResponse) => void,
  ) => {
    const handle = async (): Promise<BackgroundResponse> => {
      try {
        switch (message.type) {
          case "BRIDGE_HEALTH":
            return { ok: true, data: { healthy: await checkHealth() } };
          case "BRIDGE_LIST_PROFILES":
            return { ok: true, data: await listProfiles() };
          case "BRIDGE_CAPTURE":
            return {
              ok: true,
              data: await captureContent(
                message.content,
                message.source,
                message.sourceUrl,
                message.profileId ?? "default",
                message.locale,
              ),
            };
          case "BRIDGE_CONTEXT_PACKET": {
            const packet = await fetchContextPacket(message.target, message.profileId);
            return { ok: true, data: packet };
          }
          case "BRIDGE_LIST_CANDIDATES":
            return { ok: true, data: await listCandidates() };
          case "BRIDGE_GET_CANDIDATE":
            return { ok: true, data: await getCandidate(message.candidateId) };
          case "BRIDGE_EVALUATE_CANDIDATE":
            return {
              ok: true,
              data: await evaluateCandidate(message.candidateId, message.level),
            };
          case "BRIDGE_DIFF_CANDIDATE":
            return { ok: true, data: await diffCandidate(message.candidateId) };
          case "BRIDGE_APPROVE_CANDIDATE": {
            const explicit = message.explicitConfirmation;
            return {
              ok: true,
              data: await approveCandidate(
                message.candidateId,
                message.forceCritical ?? false,
                message.overrideReason,
                explicit
                  ? {
                      section: explicit.section,
                      checked: true,
                      reason: explicit.reason,
                      confirmed_at: explicit.confirmedAt,
                    }
                  : undefined,
              ),
            };
          }
          case "BRIDGE_REJECT_CANDIDATE":
            return {
              ok: true,
              data: await rejectCandidate(message.candidateId, message.reason),
            };
          case "CAPTURE_SELECTION": {
            const text = await readSelectionFromTab(message.tabId);
            if (!text) {
              return { ok: false, error: "No text selected" };
            }
            const tab = await chrome.tabs.get(message.tabId);
            const captured = await captureContent(
              text,
              "selection",
              tab.url ?? undefined,
              message.profileId ?? "default",
              message.locale,
              {
                rawContent: text,
                userSelected: true,
                captureSource: "selection",
                captureConfidence: "high",
                requiresReview: false,
              },
            );
            await finishCaptureFlow(message.windowId, captured, {
              source: "selection",
              profileId: message.profileId ?? "default",
              rawCaptureText: text,
            });
            return { ok: true, data: captured };
          }
          case "CAPTURE_PAGE": {
            const page = await readPageFromTab(message.tabId);
            if (!page.cleaned) {
              return { ok: false, error: "Could not read page" };
            }
            const tab = await chrome.tabs.get(message.tabId);
            const warnings: string[] = ["page_capture_low_confidence"];
            if (page.uiNoiseDetected) warnings.push("ui_noise_detected");
            if (page.extractor === "fallback") warnings.push("fallback_extractor_used");
            const captured = await captureContent(
              page.cleaned,
              "page",
              tab.url ?? undefined,
              message.profileId ?? "default",
              message.locale,
              {
                rawContent: page.raw,
                userSelected: false,
                captureSource: "page",
                captureConfidence: "low",
                requiresReview: true,
                captureWarnings: warnings,
                extractor: page.extractor,
              },
            );
            await finishCaptureFlow(message.windowId, captured, {
              source: "page",
              profileId: message.profileId ?? "default",
              rawCaptureText: page.raw ?? page.cleaned,
            });
            return { ok: true, data: captured };
          }
          case "CAPTURE_CLIPBOARD": {
            const text = message.content.trim();
            if (!text) {
              return { ok: false, error: "Clipboard is empty" };
            }
            const captured = await captureContent(
              text,
              "clipboard",
              undefined,
              message.profileId ?? "default",
              message.locale,
              {
                rawContent: text,
                userSelected: true,
                captureSource: "clipboard",
                captureConfidence: "high",
                requiresReview: false,
                captureWarnings: message.captureWarnings ?? [],
              },
            );
            await finishCaptureFlow(message.windowId, captured, {
              source: "clipboard",
              profileId: message.profileId ?? "default",
              rawCaptureText: text,
            });
            return { ok: true, data: captured };
          }
          case "INSERT_CONTEXT_PACKET": {
            const packet = await fetchContextPacket(message.target, message.profileId);
            const text = formatContextPacketForInsert(packet);
            const inserted = await insertTextInTab(message.tabId, text, message.target);
            if ("ok" in inserted && inserted.ok === false) {
              const hint = "hint" in inserted ? inserted.hint : undefined;
              const code = "code" in inserted ? inserted.code : undefined;
              return {
                ok: false,
                error: [inserted.error, code, hint].filter(Boolean).join(" — "),
              };
            }
            return { ok: true, data: { inserted: true } };
          }
          case "OPEN_SIDE_PANEL": {
            if (message.windowId != null) {
              await chrome.sidePanel.open({ windowId: message.windowId });
            }
            return { ok: true };
          }
          case "CANDIDATES_CHANGED":
            return { ok: true };
          default:
            return { ok: false, error: "Unknown message type" };
        }
      } catch (err) {
        if (err instanceof BridgeError) {
          return { ok: false, error: err.message, errorDetails: err.details };
        }
        return { ok: false, error: String(err) };
      }
    };

    handle().then(sendResponse);
    return true;
  },
);

chrome.runtime.onInstalled.addListener(() => {
  console.info("[Sayane] extension installed (Phase 3)");
  void chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: false });
});
