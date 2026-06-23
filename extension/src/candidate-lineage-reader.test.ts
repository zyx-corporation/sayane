import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";
import test from "node:test";

import { readCandidateLineage } from "./candidate-lineage-reader.ts";
import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateLineage,
} from "./types.js";

const extRoot = dirname(fileURLToPath(import.meta.url));

test("background and types expose candidate lineage message variant", () => {
  const typesSrc = readFileSync(join(extRoot, "types.ts"), "utf8");
  assert.ok(typesSrc.includes('type: "BRIDGE_GET_CANDIDATE_LINEAGE"'));

  const backgroundSrc = readFileSync(join(extRoot, "background.ts"), "utf8");
  assert.ok(backgroundSrc.includes('case "BRIDGE_GET_CANDIDATE_LINEAGE"'));
});

test("candidate lineage reader sends lineage message and unwraps data", async () => {
  const expected: CandidateLineage = {
    capture_id: "cap-1",
    candidate_id: "cand-1",
    profile_id: "default",
    status: "evaluated",
    decision: "evaluated",
    captured_at: "2026-06-20T00:00:00Z",
    events: [],
  };
  const sent: BackgroundMessage[] = [];
  const send = async (message: BackgroundMessage): Promise<BackgroundResponse> => {
    sent.push(message);
    return { ok: true, data: expected };
  };

  const actual = await readCandidateLineage(send, "cand-1");
  assert.deepEqual(sent, [{ type: "BRIDGE_GET_CANDIDATE_LINEAGE", candidateId: "cand-1" }]);
  assert.deepEqual(actual, expected);
});

test("candidate lineage reader throws on background error", async () => {
  const send = async (): Promise<BackgroundResponse> => ({
    ok: false,
    error: "lineage unavailable",
  });

  await assert.rejects(() => readCandidateLineage(send, "cand-1"), /lineage unavailable/);
});
