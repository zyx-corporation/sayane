import assert from "node:assert/strict";
import { existsSync, readFileSync, readdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it } from "node:test";
import { CONTENT_SCRIPT_BUNDLE } from "./content-script-bundle.js";

const extRoot = join(dirname(fileURLToPath(import.meta.url)), "..");

describe("content script bundle / manifest", () => {
  it("manifest content_scripts references the bundle file that exists on disk", () => {
    const manifest = JSON.parse(
      readFileSync(join(extRoot, "manifest.json"), "utf8"),
    ) as {
      content_scripts?: Array<{ js?: string[] }>;
    };
    const scriptPaths = (manifest.content_scripts ?? []).flatMap((entry) => entry.js ?? []);
    assert.ok(scriptPaths.length > 0, "content_scripts must list at least one js file");
    assert.equal(scriptPaths.length, 1, "content script must be a single bundled file");

    for (const rel of scriptPaths) {
      assert.equal(rel, CONTENT_SCRIPT_BUNDLE, "manifest must reference CONTENT_SCRIPT_BUNDLE");
      const abs = join(extRoot, rel);
      assert.ok(existsSync(abs), `${rel} must exist after build`);
    }
  });

  it("bundle has no ES module import/export and is not split into chunks", () => {
    const bundlePath = join(extRoot, CONTENT_SCRIPT_BUNDLE);
    const bundle = readFileSync(bundlePath, "utf8");
    assert.ok(!/^\s*import\s/m.test(bundle), "bundle must not use import");
    assert.ok(!/^\s*export\s/m.test(bundle), "bundle must not use export");
    assert.ok(
      bundle.startsWith('"use strict"') || bundle.includes("(() =>"),
      "bundle should be IIFE",
    );

    const distFiles = readdirSync(join(extRoot, "dist"));
    const forbidden = distFiles.filter(
      (name) =>
        name.endsWith(".js") &&
        !name.endsWith(".map") &&
        (name === "content.js" ||
          /^vendor.*\.js$/.test(name) ||
          /^provider-.*\.js$/.test(name)),
    );
    assert.deepEqual(
      forbidden,
      [],
      `unexpected split/legacy content script files: ${forbidden.join(", ")}`,
    );
  });

  it("bundle includes Sayane load log and SAYANE_PING handler", () => {
    const bundle = readFileSync(join(extRoot, CONTENT_SCRIPT_BUNDLE), "utf8");
    assert.ok(bundle.includes("[Sayane] content script loaded"));
    assert.ok(bundle.includes("SAYANE_PING"));
    assert.ok(bundle.includes("onMessage.addListener"));
  });
});
