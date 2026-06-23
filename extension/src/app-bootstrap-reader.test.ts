import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { readAppContract, readAppOverview } from "./app-bootstrap-reader.ts";
import type {
  BackgroundMessage,
  BackgroundResponse,
  ResidentAppContract,
  ResidentAppOverview,
} from "./types.js";

const extRoot = dirname(fileURLToPath(import.meta.url));

test("bridge client exposes app bootstrap fetchers", () => {
  const src = readFileSync(join(extRoot, "bridge-client.ts"), "utf8");
  assert.ok(src.includes("getAppContract"));
  assert.ok(src.includes('"/app/contract"'));
  assert.ok(src.includes("getAppOverview"));
  assert.ok(src.includes('"/app/overview"'));
});

test("background and types expose app bootstrap message variants", () => {
  const typesSrc = readFileSync(join(extRoot, "types.ts"), "utf8");
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_APP_CONTRACT"'));
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_APP_OVERVIEW"'));

  const backgroundSrc = readFileSync(join(extRoot, "background.ts"), "utf8");
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_APP_CONTRACT"'));
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_APP_OVERVIEW"'));
});

test("bootstrap reader sends contract message and unwraps data", async () => {
  const expected: ResidentAppContract = {
    kind: "resident_app_contract",
    contract_version: "1",
    preferred_entrypoint: "/app/overview",
    human_surfaces: [],
    read_surfaces: [],
    write_surfaces: [],
    recommended_flow: [],
    screen_state_contracts: [],
    boundaries: [],
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readAppContract(send);
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_APP_CONTRACT" }]);
  assert.deepEqual(actual, expected);
});

test("bootstrap reader sends overview message and unwraps data", async () => {
  const expected: ResidentAppOverview = {
    kind: "resident_app_overview",
    profile_id: "default",
    runtime: {},
    summary: {},
    review_summary: {},
    mcp_summary: {},
    daemon_summary: {},
    review_queue: {},
    mcp_preview: {},
    daemon_overview: {},
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readAppOverview(send);
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_APP_OVERVIEW" }]);
  assert.deepEqual(actual, expected);
});
