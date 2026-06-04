import assert from "node:assert/strict";
import test from "node:test";
import { mapKnownCoreMessage, toUserFacingError } from "./bridge-error-format.js";

test("unsupported merge error is mapped to user-facing message", () => {
  const message = toUserFacingError({
    message: "Unsupported merge section: important_terms",
  }, "ja");
  assert.equal(
    message,
    "この候補はまだ自動保存に対応していない種類です。保存先セクションの対応が必要です。",
  );
  assert.ok(!message.includes("Unsupported merge section"));
});

test("mapKnownCoreMessage never returns raw unsupported merge text", () => {
  const msg = mapKnownCoreMessage("Unsupported merge section: persona", "ja");
  assert.ok(!msg.includes("Unsupported merge section"));
});
