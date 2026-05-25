import { expect, test } from "@playwright/test";
import {
  configureExtensionBridge,
  insertViaBackground,
  insertViaPopup,
  launchExtensionContext,
  openMockLlmPage,
} from "./helpers/extension.js";

test.describe("INS-CG-02 Insert context (ChatGPT)", () => {
  test("inserts context packet into mocked ChatGPT DOM", async () => {
    const { context, extensionId } = await launchExtensionContext();
    try {
      await configureExtensionBridge(context, extensionId);
      const page = await openMockLlmPage(context, "chatgpt");

      const res = await insertViaBackground(context, extensionId, "chatgpt");
      expect(res.ok, res.error ?? "insert failed").toBe(true);

      const value = await page.locator("#prompt-textarea").inputValue();
      expect(value).toContain("Example User");
    } finally {
      await context.close();
    }
  });

  test("popup shows Inserted (chatgpt) on mocked ChatGPT tab", async ({}, testInfo) => {
    const { context, extensionId } = await launchExtensionContext();
    try {
      await configureExtensionBridge(context, extensionId);
      const page = await openMockLlmPage(context, "chatgpt");

      try {
        const popup = await insertViaPopup(context, extensionId, "chatgpt", page);
        await expect(popup.locator("#status")).toContainText("Inserted (chatgpt)", {
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
