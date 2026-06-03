/** Shared cursor rules for popup, options, and diff (injected via <style> or duplicated in HTML). */

export const BUSY_CURSOR_CSS = `
  body.is-busy,
  body.is-busy #app-root {
    cursor: wait;
  }
  button:disabled[data-cursor-hint="busy"] {
    cursor: wait !important;
  }
  button:disabled[data-cursor-hint="unavailable"] {
    cursor: not-allowed !important;
  }
  button:disabled:not([data-cursor-hint]) {
    cursor: not-allowed !important;
  }
`;
