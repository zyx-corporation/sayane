import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateLineage,
} from "./types.js";

export type CandidateLineageMessageSender = (
  message: BackgroundMessage,
) => Promise<BackgroundResponse>;

export async function readCandidateLineage(
  send: CandidateLineageMessageSender,
  candidateId: string,
): Promise<CandidateLineage> {
  const response = await send({
    type: "BRIDGE_GET_CANDIDATE_LINEAGE",
    candidateId,
  });
  if (!response.ok) {
    throw new Error(response.error);
  }
  return response.data as CandidateLineage;
}
