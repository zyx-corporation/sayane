export type RealSiteId = "chatgpt" | "claude";

export type FailureKind =
  | "SAYANE_REGRESSION"
  | "DOM_DRIFT"
  | "AUTH_REQUIRED"
  | "PERMISSION_ERROR"
  | "NETWORK_OR_RATE_LIMIT"
  | "ENVIRONMENT_ERROR";

export type RealSiteSpec = {
  id: RealSiteId;
  target: "chatgpt" | "claude";
  url: string;
  storageStateEnv: string;
  loginIndicators: readonly string[];
  readinessSelectors: readonly string[];
  inputSelectors: readonly string[];
};

export type SelectorMatch = {
  selector: string;
  count: number;
  visibleCount: number;
};

export type EditableCandidate = {
  tagName: string;
  role: string | null;
  ariaLabel: string | null;
  placeholder: string | null;
  contentEditable: string;
  textLength: number;
  visible: boolean;
};

export type SelectorReport = {
  site: RealSiteId;
  url: string;
  title: string;
  matches: SelectorMatch[];
  editableCandidates: EditableCandidate[];
};
