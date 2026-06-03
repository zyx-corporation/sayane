import assert from "node:assert/strict";
import { describe, it } from "node:test";
import type { OptionsUpdatedMessage } from "./options-notify.js";

describe("options notify message", () => {
  it("has stable shape for popup listener", () => {
    const message: OptionsUpdatedMessage = {
      type: "SAYANE_OPTIONS_UPDATED",
      bridgeUrl: "http://127.0.0.1:38741",
      defaultProfileId: "default",
    };
    assert.equal(message.type, "SAYANE_OPTIONS_UPDATED");
    assert.ok(!("bridgeToken" in message));
  });
});
