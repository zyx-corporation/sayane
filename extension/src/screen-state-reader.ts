import type {
  BackgroundMessage,
  BackgroundResponse,
  CandidateDetailScreenState,
  CandidateQueueScreenState,
  DaemonPanelScreenState,
  HomeScreenState,
} from "./types.js";

export type ScreenStateMessageSender = (
  message: BackgroundMessage,
) => Promise<BackgroundResponse>;

async function readScreenState<T>(
  send: ScreenStateMessageSender,
  message: BackgroundMessage,
): Promise<T> {
  const response = await send(message);
  if (!response.ok) {
    throw new Error(response.error);
  }
  return response.data as T;
}

export async function readHomeScreenState(
  send: ScreenStateMessageSender,
): Promise<HomeScreenState> {
  return readScreenState<HomeScreenState>(send, {
    type: "BRIDGE_GET_HOME_SCREEN_STATE",
  });
}

export async function readCandidateQueueScreenState(
  send: ScreenStateMessageSender,
): Promise<CandidateQueueScreenState> {
  return readScreenState<CandidateQueueScreenState>(send, {
    type: "BRIDGE_GET_CANDIDATE_QUEUE_SCREEN_STATE",
  });
}

export async function readCandidateDetailScreenState(
  send: ScreenStateMessageSender,
  candidateId: string,
): Promise<CandidateDetailScreenState> {
  return readScreenState<CandidateDetailScreenState>(send, {
    type: "BRIDGE_GET_CANDIDATE_DETAIL_SCREEN_STATE",
    candidateId,
  });
}

export async function readDaemonPanelScreenState(
  send: ScreenStateMessageSender,
): Promise<DaemonPanelScreenState> {
  return readScreenState<DaemonPanelScreenState>(send, {
    type: "BRIDGE_GET_DAEMON_PANEL_SCREEN_STATE",
  });
}
