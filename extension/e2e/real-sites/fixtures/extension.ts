import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { chromium, type BrowserContext } from "@playwright/test";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export type LoadedExtension = {
  context: BrowserContext;
  extensionId: string;
  close: () => Promise<void>;
};

export async function loadSayaneExtension(options?: {
  userDataDir?: string;
}): Promise<LoadedExtension> {
  const extensionDir = path.resolve(__dirname, "../../../");
  const userDataDir = options?.userDataDir
    ? path.resolve(options.userDataDir)
    : path.resolve(
        process.cwd(),
        ".playwright-real-dom-user-data",
        `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      );

  fs.mkdirSync(userDataDir, { recursive: true });

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${extensionDir}`,
      `--load-extension=${extensionDir}`,
    ],
  });

  let [serviceWorker] = context.serviceWorkers();
  if (!serviceWorker) {
    serviceWorker = await context.waitForEvent("serviceworker", { timeout: 15_000 });
  }

  const extensionId = new URL(serviceWorker.url()).host;
  return {
    context,
    extensionId,
    close: () => context.close(),
  };
}

export async function configureExtension(
  context: BrowserContext,
  extensionId: string,
  config: { bridgeUrl: string; bridgeToken: string; defaultProfileId?: string },
): Promise<void> {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/options.html`);

  await page.evaluate(async (payload) => {
    await chrome.storage.sync.set({
      bridgeUrl: payload.bridgeUrl,
      bridgeToken: payload.bridgeToken,
      defaultProfileId: payload.defaultProfileId ?? "default",
      displayLanguage: "en",
    });
  }, config);

  await page.close();
}

export async function findTabIdForUrl(
  context: BrowserContext,
  extensionId: string,
  urlPrefix: string,
): Promise<number> {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/options.html`);
  const tabId = await page.evaluate(async (prefix) => {
    const tabs = await chrome.tabs.query({});
    const match = tabs.find((tab) => typeof tab.url === "string" && tab.url.startsWith(prefix));
    if (!match?.id) {
      throw new Error(`Could not find tab for ${prefix}`);
    }
    return match.id;
  }, urlPrefix);
  await page.close();
  return tabId;
}

export async function sendInsertMessage(
  context: BrowserContext,
  extensionId: string,
  payload: { tabId: number; target: "chatgpt" | "claude"; profileId?: string },
): Promise<{ ok: boolean; data?: unknown; error?: string }> {
  const page = await context.newPage();
  await page.goto(`chrome-extension://${extensionId}/options.html`);
  const response = await page.evaluate(async (messagePayload) => {
    return chrome.runtime.sendMessage({
      type: "INSERT_CONTEXT_PACKET",
      tabId: messagePayload.tabId,
      target: messagePayload.target,
      profileId: messagePayload.profileId ?? "default",
    });
  }, payload);
  await page.close();
  return response as { ok: boolean; data?: unknown; error?: string };
}
