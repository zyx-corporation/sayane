import fs from "node:fs/promises";
import path from "node:path";
import type { Page, TestInfo } from "@playwright/test";
import type { FailureKind, RealSiteSpec, SelectorReport } from "./types";

export class ClassifiedE2EError extends Error {
  constructor(
    readonly kind: FailureKind,
    message: string,
  ) {
    super(message);
    this.name = "ClassifiedE2EError";
  }
}

export async function detectAuthRequired(page: Page, spec: RealSiteSpec): Promise<boolean> {
  for (const selector of spec.loginIndicators) {
    try {
      if ((await page.locator(selector).count()) > 0) return true;
    } catch {
      // Some text regex selectors can fail on unusual pages; ignore and continue.
    }
  }
  const url = page.url().toLowerCase();
  return url.includes("login") || url.includes("auth") || url.includes("signin");
}

export async function waitForRealSiteReady(page: Page, spec: RealSiteSpec): Promise<void> {
  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    if (await detectAuthRequired(page, spec)) {
      throw new ClassifiedE2EError(
        "AUTH_REQUIRED",
        `${spec.id}: login/session is required before running real DOM E2E`,
      );
    }
    for (const selector of spec.readinessSelectors) {
      try {
        const first = page.locator(selector).first();
        if ((await first.count()) > 0 && (await first.isVisible({ timeout: 500 }).catch(() => false))) {
          return;
        }
      } catch {
        // Continue probing other selectors.
      }
    }
    await page.waitForTimeout(500);
  }
  throw new ClassifiedE2EError(
    "DOM_DRIFT",
    `${spec.id}: no ready input candidate matched before timeout`,
  );
}

export async function buildSelectorReport(page: Page, spec: RealSiteSpec): Promise<SelectorReport> {
  return page.evaluate((siteSpec) => {
    const isVisible = (el: Element): boolean => {
      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      return rect.width > 0 && rect.height > 0 && style.visibility !== "hidden" && style.display !== "none";
    };

    const matches = siteSpec.inputSelectors.map((selector) => {
      const nodes = Array.from(document.querySelectorAll(selector));
      return {
        selector,
        count: nodes.length,
        visibleCount: nodes.filter(isVisible).length,
      };
    });

    const editableNodes = Array.from(
      document.querySelectorAll('textarea, input, [contenteditable="true"], [role="textbox"]'),
    ).slice(0, 50);

    const editableCandidates = editableNodes.map((node) => {
      const el = node as HTMLElement;
      return {
        tagName: el.tagName,
        role: el.getAttribute("role"),
        ariaLabel: el.getAttribute("aria-label"),
        placeholder: el.getAttribute("placeholder"),
        contentEditable: el.getAttribute("contenteditable") ?? "",
        textLength:
          el instanceof HTMLInputElement || el instanceof HTMLTextAreaElement
            ? el.value.length
            : (el.textContent ?? "").length,
        visible: isVisible(el),
      };
    });

    return {
      site: siteSpec.id,
      url: location.href,
      title: document.title,
      matches,
      editableCandidates,
    };
  }, spec);
}

export async function sanitizeDomSnapshot(page: Page): Promise<string> {
  return page.evaluate(() => {
    const clone = document.documentElement.cloneNode(true) as HTMLElement;
    clone.querySelectorAll("script, style, svg, canvas, img, video, audio").forEach((node) => node.remove());
    clone.querySelectorAll("input, textarea").forEach((node) => {
      node.setAttribute("value", "[redacted]");
    });
    const html = clone.outerHTML;
    return html.length > 250_000 ? `${html.slice(0, 250_000)}\n<!-- truncated -->` : html;
  });
}

export async function writeDiagnostics(
  page: Page,
  spec: RealSiteSpec,
  testInfo: TestInfo,
  reason: string,
): Promise<void> {
  const dir = testInfo.outputPath(`${spec.id}-diagnostics`);
  await fs.mkdir(dir, { recursive: true });

  const report = await buildSelectorReport(page, spec).catch((err) => ({
    site: spec.id,
    url: page.url(),
    title: "unknown",
    matches: [],
    editableCandidates: [],
    error: String(err),
  }));
  await fs.writeFile(path.join(dir, "selector-report.json"), JSON.stringify(report, null, 2));

  const snapshot = await sanitizeDomSnapshot(page).catch((err) => `snapshot failed: ${String(err)}`);
  await fs.writeFile(path.join(dir, "dom-snapshot.sanitized.html"), snapshot);

  await fs.writeFile(
    path.join(dir, "failure.txt"),
    [`reason=${reason}`, `url=${page.url()}`, `title=${await page.title().catch(() => "unknown")}`].join("\n"),
  );

  await page.screenshot({ path: path.join(dir, "screenshot.png"), fullPage: true }).catch(() => undefined);
}
