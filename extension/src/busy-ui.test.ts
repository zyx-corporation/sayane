import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  BusyUiController,
  applyCursorHint,
  createEmptyBusyState,
  isBusyState,
} from "./busy-ui.js";

function mockButton(label: string): HTMLButtonElement {
  let hint: string | null = null;
  return {
    disabled: false,
    textContent: label,
    setAttribute(name: string, value: string) {
      if (name === "data-cursor-hint") hint = value;
    },
    removeAttribute(name: string) {
      if (name === "data-cursor-hint") hint = null;
    },
    getAttribute(name: string) {
      return name === "data-cursor-hint" ? hint : null;
    },
  } as unknown as HTMLButtonElement;
}

describe("busy-ui", () => {
  it("isBusyState is false when all flags are false", () => {
    assert.equal(isBusyState(createEmptyBusyState()), false);
  });

  it("isBusyState is true when any flag is true", () => {
    const state = createEmptyBusyState();
    state.evaluating = true;
    assert.equal(isBusyState(state), true);
  });

  it("begin/end toggles aria-busy on root", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = {
      setAttribute: (() => {}) as HTMLElement["setAttribute"],
    } as HTMLElement;
    let ariaBusy = "false";
    root.setAttribute = (name: string, value: string) => {
      if (name === "aria-busy") ariaBusy = value;
    };
    const ctrl = new BusyUiController(root, doc);
    ctrl.begin("evaluating");
    assert.equal(ariaBusy, "true");
    ctrl.end("evaluating");
    assert.equal(ariaBusy, "false");
  });

  it("run clears busy flag after rejection", async () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const ctrl = new BusyUiController(root, doc);
    await assert.rejects(
      () =>
        ctrl.run("evaluating", async () => {
          throw new Error("fail");
        }),
      /fail/,
    );
    assert.equal(ctrl.getState().evaluating, false);
  });

  it("registerButton shows busy label while operation runs", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const btn = mockButton("評価");
    const ctrl = new BusyUiController(root, doc);
    ctrl.registerButton("evaluate", btn, {
      busyKey: "evaluating",
      idleLabel: "評価",
      busyLabel: "評価中...",
    });
    ctrl.begin("evaluating");
    assert.equal(btn.textContent, "評価中...");
    assert.equal(btn.disabled, true);
    ctrl.end("evaluating");
    assert.equal(btn.textContent, "評価");
  });

  it("blockDuringCandidateMutation disables approve without busy label while rejecting", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const approve = mockButton("承認");
    const ctrl = new BusyUiController(root, doc);
    ctrl.registerButton("approve", approve, {
      busyKey: "approving",
      idleLabel: "承認",
      busyLabel: "承認中...",
      blockDuringCandidateMutation: true,
    });
    ctrl.begin("rejecting");
    assert.equal(approve.disabled, true);
    assert.equal(approve.getAttribute("data-cursor-hint"), "busy");
    assert.equal(approve.textContent, "承認");
    ctrl.end("rejecting");
  });

  it("sets wait cursor hint on button disabled by its own busy operation", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const btn = mockButton("評価");
    const ctrl = new BusyUiController(root, doc);
    ctrl.registerButton("evaluate", btn, {
      busyKey: "evaluating",
      idleLabel: "評価",
      busyLabel: "評価中...",
    });
    ctrl.begin("evaluating");
    assert.equal(btn.getAttribute("data-cursor-hint"), "busy");
    ctrl.end("evaluating");
    assert.equal(btn.getAttribute("data-cursor-hint"), null);
  });

  it("applyExternalDisabled uses unavailable hint when idle and blocked by rules", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const btn = mockButton("Capture");
    const ctrl = new BusyUiController(root, doc);
    ctrl.registerButton("capture", btn, {
      busyKey: "capturing",
      idleLabel: "Capture",
      busyLabel: "Capturing...",
    });
    ctrl.applyExternalDisabled("capture", true);
    assert.equal(btn.disabled, true);
    assert.equal(btn.getAttribute("data-cursor-hint"), "unavailable");
  });

  it("applyExternalDisabled uses busy hint when globally busy", () => {
    const doc = {
      body: { classList: { add: () => {}, remove: () => {} } },
    } as unknown as Document;
    const root = { setAttribute: () => {} } as HTMLElement;
    const btn = mockButton("Capture");
    const ctrl = new BusyUiController(root, doc);
    ctrl.registerButton("capture", btn, {
      busyKey: "capturing",
      idleLabel: "Capture",
      busyLabel: "Capturing...",
    });
    ctrl.begin("pairing");
    ctrl.applyExternalDisabled("capture", true);
    assert.equal(btn.getAttribute("data-cursor-hint"), "busy");
    ctrl.end("pairing");
  });

  it("applyCursorHint clears hint when re-enabled", () => {
    const btn = mockButton("x");
    applyCursorHint(btn, "unavailable");
    assert.equal(btn.getAttribute("data-cursor-hint"), "unavailable");
    applyCursorHint(btn, null);
    assert.equal(btn.getAttribute("data-cursor-hint"), null);
  });
});
