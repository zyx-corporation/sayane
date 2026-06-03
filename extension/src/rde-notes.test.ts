import assert from "node:assert/strict";
import { describe, it } from "node:test";
import { formatEvaluationNote, formatEvaluationNotes } from "./rde-notes.js";

describe("rde-notes", () => {
  it("localizes imperative heuristic note for ja", () => {
    const text = formatEvaluationNote(
      { source: "heuristic", key: "imperative_or_overconfident_phrasing", params: {} },
      "ja",
    );
    assert.match(text, /命令的/);
    assert.doesNotMatch(text, /Imperative/);
  });

  it("localizes LLM judge result line for ja", () => {
    const text = formatEvaluationNote("LLM judge (gpt-4o-mini): Suspicious Drift", "ja");
    assert.match(text, /gpt-4o-mini/);
    assert.match(text, /疑わしい逸脱/);
  });

  it("prefixes unknown LLM notes in ja", () => {
    const text = formatEvaluationNote(
      { source: "llm_judge", text: "Some novel explanation." },
      "ja",
    );
    assert.match(text, /^LLM judgeの指摘:/);
  });

  it("keeps english for en locale", () => {
    const text = formatEvaluationNote(
      { source: "heuristic", key: "imperative_or_overconfident_phrasing", params: {} },
      "en",
    );
    assert.match(text, /Imperative or overconfident/);
  });

  it("formats bullet list", () => {
    const block = formatEvaluationNotes(
      [
        { source: "heuristic", key: "imperative_or_overconfident_phrasing", params: {} },
        "LLM judge (gpt-4o-mini): Suspicious Drift",
      ],
      "ja",
    );
    assert.match(block, /^- /);
    assert.match(block, /\n- /);
  });
});
