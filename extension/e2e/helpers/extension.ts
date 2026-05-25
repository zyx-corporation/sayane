import fs from "node:fs";
import path from "node:path";
import type { BrowserContext, Page } from "@playwright/test";
import { chromium, expect } from "@playwright/test";

const EXTENSION_DIR = path.resolve(__dirname, "../..");
const E2E_ENV_FILE = path.join(EXTENSION_DIR, "e2e", ".e2e-env.json");

export type E2eEnv = {
  bridgeUrl: string;
  token: string;
  home: string;
};

export function loadE2eEnv(): E2eEnv {
  return JSON.parse(fs.readFileSync(E2E_ENV_FILE, "utf8")) as E2eEnv;
}

export async function launchExtensionContext(): Promise<{
  context: BrowserContext;
  extensionId: string;
}> {
  const context = await chromium.launchPersistentContext("", {
    channel: "chromium",
    headless: false,
    args: [
      `--disable-extensions-except=${EXTENSION_DIR}`,
      `--load-extension=${EXTENSION_DIR}`,
    ],
  });

  let serviceWorker = context.serviceWorkers()[0];
  if (!serviceWorker) {
    serviceWorker = await context.waitForEvent("serviceworker", { timeout: 15_000 });
  }
  const extensionId = serviceWorker.url().split("/")[2];
  if (!extensionId) {
    throw new Error(`Could not parse extension id from ${serviceWorker.url()}`);
  }

  return { context, extensionId };
}

export async function configureExtensionBridge(
  context: BrowserContext,
  extensionId: string,
): Promise<void> {
  const env = loadE2eEnv();
  const optionsPage = await context.newPage();
  await optionsPage.goto(`chrome-extension://${extensionId}/options.html`);
  await optionsPage.locator("#bridge-url").fill(env.bridgeUrl);
  await optionsPage.locator("#bridge-token").fill(env.token);
  await optionsPage.locator("#default-profile").fill("default");
  await optionsPage.locator("#save").click();
  await expect(optionsPage.locator("#status")).not.toHaveClass(/error/, { timeout: 5000 });
  await optionsPage.close();
}

function fixtureHtml(name: "chatgpt" | "claude"): string {
  return fs.readFileSync(
    path.join(EXTENSION_DIR, "e2e", "fixtures", `${name}.html`),
    "utf8",
  );
}

export async function mockLlmSite(page: Page, site: "chatgpt" | "claude"): Promise<void> {
  const host = site === "chatgpt" ? "chatgpt.com" : "claude.ai";
  const body = fixtureHtml(site);
  await page.route(`https://${host}/**`, async (route) => {
    await route.fulfill({ status: 200, contentType: "text/html", body });
  });
}

export async function openMockLlmPage(
  context: BrowserContext,
  site: "chatgpt" | "claude",
): Promise<Page> {
  const host = site === "chatgpt" ? "chatgpt.com" : "claude.ai";
  const page = await context.newPage();
  await mockLlmSite(page, site);
  await page.goto(`https://${host}/`, { waitUntil: "domcontentloaded" });
  if (site === "chatgpt") {
    await page.waitForSelector("#prompt-textarea");
  } else {
    await page.waitForSelector('div[contenteditable="true"].ProseMirror');
  }
  await page.bringToFront();
  return page;
}

type BackgroundResponse = { ok: boolean; error?: string; data?: unknown };

async function extensionHelperPage(
  context: BrowserContext,
  extensionId: string,
): Promise<Page> {
  const helper = await context.newPage();
  await helper.goto(`chrome-extension://${extensionId}/popup.html`);
  await helper.waitForSelector("#btn-insert-chatgpt", { timeout: 10_000 });
  return helper;
}

function tabUrlPattern(site: "chatgpt" | "claude"): string {
  return site === "chatgpt" ? "*://chatgpt.com/*" : "*://claude.ai/*";
}

/** Drive INSERT_CONTEXT_PACKET through the background worker (popup context). */
export async function insertViaBackground(
  context: BrowserContext,
  extensionId: string,
  target: "chatgpt" | "claude",
  profileId = "default",
  tabSite: "chatgpt" | "claude" = target,
): Promise<BackgroundResponse> {
  const urlPattern = tabUrlPattern(tabSite);
  const helper = await extensionHelperPage(context, extensionId);
  const res = await helper.evaluate(
    async ({ urlPattern, target, profileId }) => {
      const tabs = await chrome.tabs.query({ url: urlPattern });
      const tabId = tabs[0]?.id;
      if (!tabId) {
        return { ok: false, error: "No matching tab for insert" };
      }
      return new Promise<BackgroundResponse>((resolve) => {
        chrome.runtime.sendMessage(
          {
            type: "INSERT_CONTEXT_PACKET",
            tabId,
            target,
            profileId,
          },
          (response) => {
            resolve((response as BackgroundResponse) ?? { ok: false, error: "No response" });
          },
        );
      });
    },
    { urlPattern, target, profileId },
  );
  await helper.close();
  return res;
}

/** Open toolbar popup after focusing the LLM tab (activeTab). */
export async function openExtensionPopup(
  context: BrowserContext,
  llmPage: Page,
): Promise<Page | null> {
  await llmPage.bringToFront();
  let serviceWorker = context.serviceWorkers()[0];
  if (!serviceWorker) {
    serviceWorker = await context.waitForEvent("serviceworker", { timeout: 15_000 });
  }
  try {
    const [popup] = await Promise.all([
      context.waitForEvent("page", {
        predicate: (p) => p.url().includes("/popup.html"),
        timeout: 5000,
      }),
      serviceWorker.evaluate(() => chrome.action.openPopup()),
    ]);
    return popup;
  } catch {
    return null;
  }
}

export async function insertViaPopup(
  context: BrowserContext,
  extensionId: string,
  target: "chatgpt" | "claude",
  llmPage: Page,
): Promise<Page> {
  const popup = await openExtensionPopup(context, llmPage);
  if (!popup) {
    throw new Error(
      "chrome.action.openPopup() unavailable; popup UI test requires toolbar popup",
    );
  }
  const buttonId =
    target === "chatgpt" ? "#btn-insert-chatgpt" : "#btn-insert-claude";
  await popup.locator(buttonId).click();
  return popup;
}
