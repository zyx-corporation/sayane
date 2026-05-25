import type { RealSiteSpec } from "./types";

export const CHATGPT_REAL_SITE: RealSiteSpec = {
  id: "chatgpt",
  target: "chatgpt",
  url: "https://chatgpt.com/",
  userDataDirEnv: "SAYANE_E2E_CHATGPT_USER_DATA_DIR",
  loginIndicators: [
    'a[href*="/auth/login"]',
    'button:has-text("Log in")',
    'button:has-text("ログイン")',
    'text=/Log in|Sign up|ログイン|サインアップ/i',
  ],
  readinessSelectors: [
    "#prompt-textarea",
    'div[contenteditable="true"]#prompt-textarea',
    'div[contenteditable="true"]',
    "textarea",
  ],
  inputSelectors: [
    "#prompt-textarea",
    "textarea[data-id]",
    "textarea[placeholder]",
    'div[contenteditable="true"]#prompt-textarea',
    'div[contenteditable="true"]',
    'div[role="textbox"]',
  ],
};

export const CLAUDE_REAL_SITE: RealSiteSpec = {
  id: "claude",
  target: "claude",
  url: "https://claude.ai/new",
  userDataDirEnv: "SAYANE_E2E_CLAUDE_USER_DATA_DIR",
  loginIndicators: [
    'a[href*="login"]',
    'button:has-text("Log in")',
    'button:has-text("ログイン")',
    'text=/Log in|Sign up|ログイン|サインアップ/i',
  ],
  readinessSelectors: [
    'div[contenteditable="true"].ProseMirror',
    'div[contenteditable="true"]',
    "fieldset textarea",
    "textarea",
    'div[role="textbox"]',
  ],
  inputSelectors: [
    'div[contenteditable="true"].ProseMirror',
    'div[contenteditable="true"]',
    "fieldset textarea",
    "textarea",
    'div[role="textbox"]',
  ],
};
