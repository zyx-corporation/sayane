import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import {
  readCandidateDetailScreenState,
  readCandidateQueueScreenState,
  readDaemonPanelScreenState,
  readHomeScreenState,
} from "./screen-state-reader.ts";
import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDetailScreenState,
  CandidateQueueScreenState,
  DaemonPanelScreenState,
  HomeScreenState,
} from "./types.js";

const extRoot = dirname(fileURLToPath(import.meta.url));

test("background and types expose screen state message variants", () => {
  const typesSrc = readFileSync(join(extRoot, "types.ts"), "utf8");
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_HOME_SCREEN_STATE"'));
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_CANDIDATE_QUEUE_SCREEN_STATE"'));
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_CANDIDATE_DETAIL_SCREEN_STATE"'));
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_DAEMON_PANEL_SCREEN_STATE"'));

  const backgroundSrc = readFileSync(join(extRoot, "background.ts"), "utf8");
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_HOME_SCREEN_STATE"'));
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_CANDIDATE_QUEUE_SCREEN_STATE"'));
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_CANDIDATE_DETAIL_SCREEN_STATE"'));
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_DAEMON_PANEL_SCREEN_STATE"'));
});

test("screen-state reader sends home message and unwraps data", async () => {
  const expected: HomeScreenState = {
    kind: "resident_app_home_screen_state",
    summary_cards: [],
    top_review_items: [],
    top_daemon_actions: [],
    quick_links: [],
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readHomeScreenState(send);
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_HOME_SCREEN_STATE" }]);
  assert.deepEqual(actual, expected);
});

test("screen-state reader sends queue message and unwraps data", async () => {
  const expected: CandidateQueueScreenState = {
    kind: "resident_app_candidate_queue_screen_state",
    reviewable_count: 1,
    status_counts: { pending: 1 },
    top_sections: [],
    items: [],
    default_sort: "captured_at_desc",
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readCandidateQueueScreenState(send);
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_CANDIDATE_QUEUE_SCREEN_STATE" }]);
  assert.deepEqual(actual, expected);
});

test("screen-state reader sends detail message with candidate id", async () => {
  const expected: CandidateDetailScreenState = {
    kind: "resident_app_candidate_detail_screen_state",
    ui_summary: {},
    allowed_actions: { approve: true },
    proposal: {},
    evaluation: {},
    diff_available: true,
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readCandidateDetailScreenState(send, "cand-1");
  assert.deepEqual(sent, [
    { type: "BRIDGE_GET_CANDIDATE_DETAIL_SCREEN_STATE", candidateId: "cand-1" },
  ]);
  assert.deepEqual(actual, expected);
});

test("screen-state reader sends daemon message and unwraps data", async () => {
  const expected: DaemonPanelScreenState = {
    kind: "resident_app_daemon_panel_screen_state",
    summary_cards: [],
    next_actions: [],
    runtime_init: {},
    cleanup_preview: {},
    repair_preview: {},
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readDaemonPanelScreenState(send);
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_DAEMON_PANEL_SCREEN_STATE" }]);
  assert.deepEqual(actual, expected);
});

test("screen-state reader throws on background error", async () => {
  const send = async (): Promise<BackgroundResponse> => ({
    ok: false,
    error: "bridge unavailable",
  });

  await assert.rejects(() => readHomeScreenState(send), /bridge unavailable/);
});
