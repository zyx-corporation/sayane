/** LLM provider adapters for context insert (DOM targets). */

export type ProviderKind = "hosted" | "local";

/** Bridge compile / context-packet target id. */
export type InsertTarget =
  | "chatgpt"
  | "claude"
  | "gemini"
  | "deepseek"
  | "local-openwebui"
  | "local-custom";

export interface ProviderAdapter {
  readonly id: InsertTarget;
  /** Bridge `target` query param (compile adapter id). */
  readonly target: string;
  /** Profile section key when building context packets. */
  readonly profileKey: string;
  readonly kind: ProviderKind;
  /** i18n key for popup insert button label. */
  readonly labelKey: string;
  /** Host patterns for manifest host_permissions (https://host/*). */
  readonly origins: readonly string[];
  /** Core Bridge `/context-packet` compile supported (must match adapters/factory.py). */
  readonly bridgeContextPacketSupported: boolean;
  matches(url: string): boolean;
  readonly inputSelectors: readonly string[];
  readonly failureHint: string;
}

export interface InsertResult {
  ok: boolean;
  error?: string;
  code?: string;
  hint?: string;
}
