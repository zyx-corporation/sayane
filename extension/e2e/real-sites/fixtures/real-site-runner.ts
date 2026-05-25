import path from "node:path";
import { expect, test } from "@playwright/test";
import { startMockBridge } from "./bridge";
import {
  configureExtension,
  findTabIdForUrl,
  loadSayaneExtension,
  sendInsertMessage,
} from "./extension";
import {
  ClassifiedE2EError,
  detectAuthRequired,
  waitForRealSiteReady,
  writeDiagnostics,
} from "./diagnostics";
import type { RealSiteSpec } from "./types";

function authProfileDir(spec: RealSiteSpec): string | undefined {
  const raw = process.env[spec.storageStateEnv];
  if (!raw) return undefined;
  return path.resolve(raw);
}

function siteOrigin(spec: RealSiteSpec): string {
  return new URL(spec.url).origin;
}

async function readEditableText(spec: RealSiteSpec, page: import("@playwright/test").Page): Promise<string> {
  return page.evaluate((selectors) => {
    for (const selector of selectors) {
      const nodes = Array.from(document.querySelectorAll(selector));
      for (const node of nodes) {
        if (!(node instanceof HTMLElement)) continue;
        if (node instanceof HTMLInputElement || node instanceof HTMLTextAreaElement) {
          if (node.value) return node.value;
        }
        const text = node.textContent ?? "";
        if (text) return text;
      }
    }
    return "";
  }, spec.inputSelectors);
}

function assertMarkerInserted(pageText: string, marker: string, siteId: string): void {
  expect(pageText, `${siteId}: inserted marker should be visible in the editable input`).toContain(marker);
}

export function defineRealSiteInsertTest(spec: RealSiteSpec): void {
  test(`${spec.id}: insert Sayane context packet into real DOM`, async ({}, testInfo) => {
    const userDataDir = authProfileDir(spec);
    test.skip(
      !userDataDir,
      `${spec.storageStateEnv} is not set; create a logged-in Chrome user data dir for ${spec.id}`,
    );

    const bridge = await startMockBridge(spec.target);
    const extension = await loadSayaneExtension({ userDataDir });

    try {
      await configureExtension(extension.context, extension.extensionId, {
        bridgeUrl: bridge.url,
        bridgeToken: bridge.token,
        defaultProfileId: "default",
      });

      const page = await extension.context.newPage();
      page.on("console", (msg) => testInfo.attach(`console-${Date.now()}.txt`, {
        body: `[${msg.type()}] ${msg.text()}`,
        contentType: "text/plain",
      }).catch(() => undefined));

      try {
        await page.goto(spec.url, { waitUntil: "domcontentloaded" });
        if (await detectAuthRequired(page, spec)) {
          throw new ClassifiedE2EError(
            "AUTH_REQUIRED",
            `${spec.id}: login/session is required before running real DOM E2E`,
          );
        }
        await waitForRealSiteReady(page, spec);

        const tabId = await findTabIdForUrl(extension.context, extension.extensionId, siteOrigin(spec));
        const response = await sendInsertMessage(extension.context, extension.extensionId, {
          tabId,
          target: spec.target,
          profileId: "default",
        });

        if (!response.ok) {
          const error = response.error ?? "unknown insert error";
          const kind = error.includes("INPUT_NOT_FOUND")
            ? "DOM_DRIFT"
            : error.includes("Cannot access") || error.includes("Cannot capture")
              ? "PERMISSION_ERROR"
              : "SAYANE_REGRESSION";
          throw new ClassifiedE2EError(kind, `${spec.id}: insert failed: ${error}`);
        }

        await expect
          .poll(() => readEditableText(spec, page), {
            message: `${spec.id}: wait for Sayane E2E marker in real editable input`,
            timeout: 10_000,
          })
          .toContain(bridge.marker);

        assertMarkerInserted(await readEditableText(spec, page), bridge.marker, spec.id);
      } catch (err) {
        const reason = err instanceof ClassifiedE2EError ? `${err.kind}: ${err.message}` : String(err);
        await writeDiagnostics(page, spec, testInfo, reason);
        if (err instanceof ClassifiedE2EError && err.kind === "AUTH_REQUIRED") {
          test.skip(true, err.message);
        }
        throw err;
      } finally {
        await page.close().catch(() => undefined);
      }
    } finally {
      await extension.close().catch(() => undefined);
      await bridge.close().catch(() => undefined);
    }
  });
}
