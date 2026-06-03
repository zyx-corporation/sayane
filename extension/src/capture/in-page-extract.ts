/**
 * Serializable entry for chrome.scripting.executeScript (no imports in injected func).
 * Logic is duplicated from page-extract-core for MV3 inject fallback.
 */

export type InPageCaptureResult = {
  raw: string;
  cleaned: string;
  provider: string;
  extractor: string;
  uiNoiseDetected: boolean;
  lowConfidence: boolean;
};

/** Runs inside the target tab when content script is not loaded yet. */
export function extractPageInDocument(): InPageCaptureResult {
  const UI_NOISE_EXACT = new Set([
    "チャット履歴",
    "新しいチャット",
    "Chat history",
    "New chat",
  ]);
  function isNoise(line: string): boolean {
    const s = line.trim();
    return s.length > 0 && UI_NOISE_EXACT.has(s);
  }
  function hostProvider(): string | null {
    const host = location.hostname;
    if (host === "chatgpt.com" || host === "chat.openai.com") return "chatgpt";
    if (host === "claude.ai") return "claude";
    if (host === "gemini.google.com") return "gemini";
    if (host.includes("deepseek.com")) return "deepseek";
    return null;
  }
  function extractChatGPT(): string {
    const turns = document.querySelectorAll("[data-message-author-role]");
    if (turns.length > 0) {
      return Array.from(turns)
        .map((n) => n.textContent?.trim() ?? "")
        .filter(Boolean)
        .join("\n\n");
    }
    return document.querySelector("main")?.innerText?.trim() ?? document.body?.innerText?.trim() ?? "";
  }
  const provider = hostProvider();
  const text = provider === "chatgpt" ? extractChatGPT() : document.body?.innerText?.trim() ?? "";
  const title = document.title || "Untitled";
  const url = location.href;
  const maxLen = 8000;
  const excerpt = text.length > maxLen ? `${text.slice(0, maxLen)}\n...[truncated]` : text;
  const kept = excerpt.split("\n").filter((l) => !isNoise(l));
  const cleaned = kept.join("\n").trim();
  return {
    raw: `Title: ${title}\nURL: ${url}\n\n${excerpt}`,
    cleaned: `Title: ${title}\nURL: ${url}\n\n${cleaned}`,
    provider: provider ?? "unknown",
    extractor: provider ?? "fallback",
    uiNoiseDetected: false,
    lowConfidence: !provider,
  };
}
