/** Site-specific DOM adapters (isolated from core logic). */

export interface SiteAdapter {
  readonly id: string;
  matches(url: string): boolean;
  /** CSS selectors tried in order until an input is found. */
  readonly inputSelectors: readonly string[];
  readonly failureHint: string;
}

export interface InsertResult {
  ok: boolean;
  error?: string;
  code?: string;
  hint?: string;
}
