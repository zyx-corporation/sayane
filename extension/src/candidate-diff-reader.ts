import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDiff,
} from "./types.js";

export type CandidateDiffMessageSender = (
  message: BackgroundMessage,
) => Promise<BackgroundResponse>;

export async function readCandidateDiff(
  send: CandidateDiffMessageSender,
  candidateId: string,
): Promise<CandidateDiff> {
  const response = await send({
    type: "BRIDGE_DIFF_CANDIDATE",
    candidateId,
  });
  if (!response.ok) {
    throw new Error(response.error);
  }
  return response.data as CandidateDiff;
}
