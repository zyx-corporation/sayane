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
  listCandidates,
  listProfiles,
  rejectCandidate,
} from "./bridge-client.js";
import {
  insertTextInTab,
  readPageFromTab,
  readSelectionFromTab,
} from "./content-script-client.js";
import type { BackgroundMessage, BackgroundResponse } from "./types.js";

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
              data: await captureContent(message.content, message.source, message.sourceUrl),
            };
          case "BRIDGE_CONTEXT_PACKET": {
            const packet = await fetchContextPacket(message.target, message.profileId);
            return { ok: true, data: packet };
          }
          case "BRIDGE_LIST_CANDIDATES":
            return { ok: true, data: await listCandidates() };
          case "BRIDGE_EVALUATE_CANDIDATE":
            return {
              ok: true,
              data: await evaluateCandidate(message.candidateId, message.level),
            };
          case "BRIDGE_DIFF_CANDIDATE":
            return { ok: true, data: await diffCandidate(message.candidateId) };
          case "BRIDGE_APPROVE_CANDIDATE":
            return {
              ok: true,
              data: await approveCandidate(
                message.candidateId,
                message.forceCritical ?? false,
              ),
            };
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
            );
            return { ok: true, data: captured };
          }
          case "CAPTURE_PAGE": {
            const text = await readPageFromTab(message.tabId);
            if (!text) {
              return { ok: false, error: "Could not read page" };
            }
            const tab = await chrome.tabs.get(message.tabId);
            const captured = await captureContent(
              text,
              "page",
              tab.url ?? undefined,
            );
            return { ok: true, data: captured };
          }
          case "INSERT_CONTEXT_PACKET": {
            const packet = await fetchContextPacket(message.target, message.profileId);
            const text = formatContextPacketForInsert(packet);
            const inserted = await insertTextInTab(message.tabId, text, message.target);
            if (!inserted.ok) {
              const hint = "hint" in inserted ? inserted.hint : undefined;
              const code = "code" in inserted ? inserted.code : undefined;
              return {
                ok: false,
                error: [inserted.error, code, hint].filter(Boolean).join(" — "),
              };
            }
            return { ok: true, data: { inserted: true } };
          }
          default:
            return { ok: false, error: "Unknown message type" };
        }
      } catch (err) {
        const msg = err instanceof BridgeError ? err.message : String(err);
        return { ok: false, error: msg };
      }
    };

    handle().then(sendResponse);
    return true;
  },
);

chrome.runtime.onInstalled.addListener(() => {
  console.info("[Omomuki] extension installed (Phase 3)");
});
