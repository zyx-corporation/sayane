import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { readCandidateDiff } from "./candidate-diff-reader.ts";
import type { BackgroundMessage, BackgroundResponse, CandidateDiff } from "./types.js";

const extRoot = dirname(fileURLToPath(import.meta.url));

test("background and types expose candidate diff message variant", () => {
  const typesSrc = readFileSync(join(extRoot, "types.ts"), "utf8");
  assert.ok(typesSrc.includes('type: "BRIDGE_DIFF_CANDIDATE"'));

  const backgroundSrc = readFileSync(join(extRoot, "background.ts"), "utf8");
  assert.ok(backgroundSrc.includes('case "BRIDGE_DIFF_CANDIDATE"'));
});

test("candidate diff reader sends diff message and unwraps data", async () => {
  const expected: CandidateDiff = {
    list_diff: {
      added: ["a"],
      removed: [],
      unchanged: ["b"],
      unchanged_count: 1,
      operation: "list_add",
    },
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readCandidateDiff(send, "cand-1");
  assert.deepEqual(sent, [{ type: "BRIDGE_DIFF_CANDIDATE", candidateId: "cand-1" }]);
  assert.deepEqual(actual, expected);
});

test("candidate diff reader throws on background error", async () => {
  const send = async (): Promise<BackgroundResponse> => ({
    ok: false,
    error: "diff unavailable",
  });

  await assert.rejects(() => readCandidateDiff(send, "cand-1"), /diff unavailable/);
});
