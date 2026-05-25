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
  storageStatePath?: string;
}): Promise<LoadedExtension> {
  const extensionDir = path.resolve(__dirname, "../../../");
  const userDataDir = path.resolve(
    process.cwd(),
    ".playwright-real-dom-user-data",
    `${Date.now()}-${Math.random().toString(36).slice(2)}`,
  );

  const context = await chromium.launchPersistentContext(userDataDir, {
    headless: false,
    args: [
      `--disable-extensions-except=${extensionDir}`,
      `--load-extension=${extensionDir}`,
    ],
    storageState: options?.storageStatePath,
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
