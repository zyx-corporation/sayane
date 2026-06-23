import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

const extRoot = dirname(fileURLToPath(import.meta.url));

test("bridge-client exposes screen state fetchers", () => {
  const src = readFileSync(join(extRoot, "bridge-client.ts"), "utf8");
  assert.ok(src.includes("getHomeScreenState"));
  assert.ok(src.includes('"/app/screen-state/home"'));
  assert.ok(src.includes("getCandidateQueueScreenState"));
  assert.ok(src.includes('"/app/screen-state/candidates"'));
  assert.ok(src.includes("getCandidateDetailScreenState"));
  assert.ok(src.includes("getDaemonPanelScreenState"));
  assert.ok(src.includes('"/app/screen-state/daemon"'));
});

test("types expose framework-neutral screen state contracts", () => {
  const src = readFileSync(join(extRoot, "types.ts"), "utf8");
  assert.ok(src.includes("export interface HomeScreenState"));
  assert.ok(src.includes("export interface CandidateQueueScreenState"));
  assert.ok(src.includes("export interface CandidateDetailScreenState"));
  assert.ok(src.includes("export interface DaemonPanelScreenState"));
});
