/** Per-candidate async action state for review cards. */

export type CandidateActionState =
  | "idle"
  | "approving"
  | "rejecting"
  | "deferring"
  | "evaluating"
  | "approved"
  | "rejected"
  | "deferred"
  | "error";

export type CardActionRecord = {
  state: CandidateActionState;
  rawError?: string;
};

export function isBusyActionState(state: CandidateActionState): boolean {
  return (
    state === "approving"
    || state === "rejecting"
    || state === "deferring"
    || state === "evaluating"
  );
}

export function isResolvedActionState(state: CandidateActionState): boolean {
  return state === "approved" || state === "rejected" || state === "deferred";
}
