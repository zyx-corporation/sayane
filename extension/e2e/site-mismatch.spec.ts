import { expect, test } from "@playwright/test";
import {
  configureExtensionBridge,
  insertViaBackground,
  launchExtensionContext,
  openMockLlmPage,
} from "./helpers/extension.js";

test.describe("INS-CG-04 site mismatch (optional)", () => {
  test("Claude insert on ChatGPT page returns SITE_MISMATCH", async () => {
    const { context, extensionId } = await launchExtensionContext();
    try {
      await configureExtensionBridge(context, extensionId);
      await openMockLlmPage(context, "chatgpt");

      const res = await insertViaBackground(
        context,
        extensionId,
        "claude",
        "default",
        "chatgpt",
      );
      expect(res.ok).toBe(false);
      expect(res.error ?? "").toMatch(/SITE_MISMATCH|does not match adapter claude/i);
    } finally {
      await context.close();
    }
  });
});
