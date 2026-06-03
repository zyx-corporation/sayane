/** Notify open extension pages that Options settings changed. */

export type OptionsUpdatedMessage = {
  type: "SAYANE_OPTIONS_UPDATED";
  bridgeUrl: string;
  defaultProfileId: string;
};

export async function notifyOptionsUpdated(
  bridgeUrl: string,
  defaultProfileId: string,
): Promise<void> {
  const message: OptionsUpdatedMessage = {
    type: "SAYANE_OPTIONS_UPDATED",
    bridgeUrl,
    defaultProfileId,
  };
  try {
    await chrome.runtime.sendMessage(message);
  } catch {
    // No listener (popup closed) — storage is the source of truth.
  }
}
