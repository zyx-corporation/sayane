/** Shared localhost URL helpers for Open WebUI vs generic local UI. */

const LOCAL_HOSTS = new Set(["localhost", "127.0.0.1", "[::1]"]);

/** Paths that are never Open WebUI chat surfaces. */
const OPENWEBUI_NON_CHAT_PREFIXES = [
  "/auth",
  "/login",
  "/register",
  "/admin",
  "/watch",
  "/error",
  "/static",
  "/api",
  "/oauth",
] as const;

export function isLocalHost(hostname: string): boolean {
  return LOCAL_HOSTS.has(hostname);
}

/**
 * Open WebUI is a SPA: chat input can appear on `/`, `/c/…`, `/home`, etc.
 * Reject only known non-chat paths (auth, admin, static assets).
 */
export function isOpenWebUIChatPath(pathname: string): boolean {
  if (OPENWEBUI_NON_CHAT_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return false;
  }
  return true;
}

export function matchesLocalOpenWebUI(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return false;
    }
    return isLocalHost(parsed.hostname) && isOpenWebUIChatPath(parsed.pathname);
  } catch {
    return false;
  }
}

export function matchesLocalCustom(url: string): boolean {
  try {
    const parsed = new URL(url);
    if (parsed.protocol !== "http:" && parsed.protocol !== "https:") {
      return false;
    }
    if (!isLocalHost(parsed.hostname)) return false;
    return !isOpenWebUIChatPath(parsed.pathname);
  } catch {
    return false;
  }
}
