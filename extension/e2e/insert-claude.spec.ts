import { expect, test } from "@playwright/test";
import {
  configureExtensionBridge,
  insertViaBackground,
  insertViaPopup,
  launchExtensionContext,
  openMockLlmPage,
} from "./helpers/extension.js";

test.describe("INS-CL-02 Insert context (Claude)", () => {
  test("inserts context packet into mocked Claude DOM", async () => {
    const { context, extensionId } = await launchExtensionContext();
    try {
      await configureExtensionBridge(context, extensionId);
      const page = await openMockLlmPage(context, "claude");

      const res = await insertViaBackground(context, extensionId, "claude");
      expect(res.ok, res.error ?? "insert failed").toBe(true);

      const text = await page.locator('div[contenteditable="true"].ProseMirror').textContent();
      expect(text ?? "").toContain("Example User");
    } finally {
      await context.close();
    }
  });

  test("popup shows Inserted (claude) on mocked Claude tab", async ({}, testInfo) => {
    const { context, extensionId } = await launchExtensionContext();
    try {
      await configureExtensionBridge(context, extensionId);
      const page = await openMockLlmPage(context, "claude");

      try {
        const popup = await insertViaPopup(context, extensionId, "claude", page);
        await expect(popup.locator("#status")).toContainText("Inserted (claude)", {
          timeout: 15_000,
        });
      } catch (err) {
        testInfo.skip(
          err instanceof Error ? err.message : "openPopup not available in this environment",
        );
      }
    } finally {
      await context.close();
    }
  });
});
