/**
 * Shared page extraction (content script + scripting fallback).
 */

export type PageExtractResult = {
  raw: string;
  cleaned: string;
  provider: string;
  extractor: string;
  uiNoiseDetected: boolean;
  lowConfidence: boolean;
  extractorError: string | null;
};

export type SayanePingResult = {
  ok: true;
  provider: string;
  url: string;
  title: string;
  readable: boolean;
  selectionTextLength: number;
  selectionCurrentLength?: number;
  selectionCachedLength?: number;
  selectionCacheAgeMs?: number | null;
  extractorAvailable: boolean;
  extractorError: string | null;
  hostPermissionOk: boolean;
  contentScriptReady: true;
};

const UI_NOISE_EXACT = new Set([
  "チャット履歴",
  "新しいチャット",
  "チャットを検索",
  "ライブラリ",
  "アプリ",
  "プロジェクト",
  "最近",
  "共有する",
  "思考時間",
  "情報源",
  "ChatGPT の回答は必ずしも正しいとは限りません",
  "ChatGPT can make mistakes. Check important info.",
  "1Passwordメニューが利用できます",
  "Chat history",
  "New chat",
  "Search chats",
  "Library",
  "Apps",
  "Projects",
  "Recent",
]);

const MIN_READABLE_CHARS = 40;

export function hostProviderFromLocation(hostname: string): string | null {
  if (hostname === "chatgpt.com" || hostname === "chat.openai.com") return "chatgpt";
  if (hostname === "claude.ai") return "claude";
  if (hostname === "gemini.google.com") return "gemini";
  if (hostname.includes("deepseek.com")) return "deepseek";
  if (hostname === "localhost" || hostname.includes("openwebui")) return "openwebui";
  return null;
}

function isUiNoiseLine(line: string): boolean {
  const s = line.trim();
  if (!s) return false;
  if (UI_NOISE_EXACT.has(s)) return true;
  if (s.startsWith("1Password") && s.length < 80) return true;
  return false;
}

function cleanText(body: string): { cleaned: string; uiNoiseDetected: boolean } {
  const lines = body.split("\n");
  let noiseHits = 0;
  const kept: string[] = [];
  for (const line of lines) {
    if (isUiNoiseLine(line)) {
      noiseHits += 1;
      continue;
    }
    kept.push(line);
  }
  const cleaned = kept.join("\n").trim();
  const uiNoiseDetected =
    noiseHits > 0 || (lines.length > 0 && noiseHits / Math.max(lines.length, 1) > 0.15);
  return { cleaned, uiNoiseDetected };
}

function extractChatGPT(): string {
  const turns = document.querySelectorAll("[data-message-author-role]");
  if (turns.length > 0) {
    return Array.from(turns)
      .map((node) => node.textContent?.trim() ?? "")
      .filter(Boolean)
      .join("\n\n");
  }
  const main = document.querySelector("main");
  return main?.innerText?.trim() ?? document.body?.innerText?.trim() ?? "";
}

function extractClaude(): string {
  const turns = document.querySelectorAll("[data-is-streaming], .font-claude-message");
  if (turns.length > 0) {
    return Array.from(turns)
      .map((node) => node.textContent?.trim() ?? "")
      .filter(Boolean)
      .join("\n\n");
  }
  return document.querySelector("main")?.innerText?.trim() ?? document.body?.innerText?.trim() ?? "";
}

function elementText(el: Element | null | undefined): string {
  if (!el) return "";
  return (el as HTMLElement).innerText?.trim() ?? "";
}

function extractGemini(): string {
  const main = document.querySelector("main, [role='main']");
  return elementText(main) || document.body?.innerText?.trim() || "";
}

function extractDeepSeek(): string {
  const main = document.querySelector("main, .chat-container, #root");
  return elementText(main) || document.body?.innerText?.trim() || "";
}

function extractOpenWebUI(): string {
  const chat = document.querySelector(".chat-messages, main, #chat-container");
  return elementText(chat) || document.body?.innerText?.trim() || "";
}

function extractFallback(): string {
  return document.body?.innerText?.trim() ?? "";
}

function extractBody(
  provider: string | null,
): { text: string; extractor: string; lowConfidence: boolean; extractorError: string | null } {
  try {
    if (provider === "chatgpt") {
      const text = extractChatGPT();
      if (!text.trim()) {
        return {
          text: "",
          extractor: "chatgpt",
          lowConfidence: true,
          extractorError: "chatgpt_empty",
        };
      }
      return { text, extractor: "chatgpt", lowConfidence: false, extractorError: null };
    }
    if (provider === "claude") {
      const text = extractClaude();
      return {
        text,
        extractor: "claude",
        lowConfidence: !text.trim(),
        extractorError: text.trim() ? null : "claude_empty",
      };
    }
    if (provider === "gemini") {
      const text = extractGemini();
      return {
        text,
        extractor: "gemini",
        lowConfidence: !text.trim(),
        extractorError: text.trim() ? null : "gemini_empty",
      };
    }
    if (provider === "deepseek") {
      const text = extractDeepSeek();
      return {
        text,
        extractor: "deepseek",
        lowConfidence: !text.trim(),
        extractorError: text.trim() ? null : "deepseek_empty",
      };
    }
    if (provider === "openwebui") {
      const text = extractOpenWebUI();
      return {
        text,
        extractor: "openwebui",
        lowConfidence: !text.trim(),
        extractorError: text.trim() ? null : "openwebui_empty",
      };
    }
    const text = extractFallback();
    return {
      text,
      extractor: "fallback",
      lowConfidence: true,
      extractorError: provider ? `${provider}_fallback` : "no_provider",
    };
  } catch (err) {
    return {
      text: "",
      extractor: provider ?? "fallback",
      lowConfidence: true,
      extractorError: String(err),
    };
  }
}

export function extractPageFromDocument(): PageExtractResult {
  const title = document.title || "Untitled";
  const url = location.href;
  const provider = hostProviderFromLocation(location.hostname);
  const { text, extractor, lowConfidence, extractorError } = extractBody(provider);
  const maxLen = 8000;
  const excerpt = text.length > maxLen ? `${text.slice(0, maxLen)}\n...[truncated]` : text;
  const raw = `Title: ${title}\nURL: ${url}\n\n${excerpt}`;
  const { cleaned, uiNoiseDetected } = cleanText(excerpt);
  const cleanedBlock = `Title: ${title}\nURL: ${url}\n\n${cleaned}`;
  return {
    raw,
    cleaned: cleanedBlock,
    provider: provider ?? "unknown",
    extractor,
    uiNoiseDetected,
    lowConfidence: lowConfidence || uiNoiseDetected,
    extractorError,
  };
}

export function buildSayanePing(hostPermissionOk = true): SayanePingResult {
  const extracted = extractPageFromDocument();
  const bodyText = extracted.cleaned.split("\n\n").slice(1).join("\n\n").trim();
  const readable = bodyText.length >= MIN_READABLE_CHARS;
  const extractorAvailable =
    extracted.extractor !== "fallback" && readable && !extracted.extractorError;
  const selectionText = window.getSelection()?.toString().trim() ?? "";

  return {
    ok: true,
    provider: extracted.provider,
    url: location.href,
    title: document.title || "",
    readable,
    selectionTextLength: selectionText.length,
    extractorAvailable,
    extractorError: extracted.extractorError,
    hostPermissionOk,
    contentScriptReady: true,
  };
}
