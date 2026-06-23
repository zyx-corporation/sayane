import type {
  BackgroundMessage,
  BackgroundResponse,
  ResidentAppContract,
  ResidentAppOverview,
} from "./types.js";

export type AppBootstrapMessageSender = (
  message: BackgroundMessage,
) => Promise<BackgroundResponse>;

async function readBootstrapPayload<T>(
  send: AppBootstrapMessageSender,
  message: BackgroundMessage,
): Promise<T> {
  const response = await send(message);
  if (!response.ok) {
    throw new Error(response.error);
  }
  return response.data as T;
}

export async function readAppContract(
  send: AppBootstrapMessageSender,
): Promise<ResidentAppContract> {
  return readBootstrapPayload<ResidentAppContract>(send, {
    type: "BRIDGE_GET_APP_CONTRACT",
  });
}

export async function readAppOverview(
  send: AppBootstrapMessageSender,
): Promise<ResidentAppOverview> {
  return readBootstrapPayload<ResidentAppOverview>(send, {
    type: "BRIDGE_GET_APP_OVERVIEW",
  });
}
