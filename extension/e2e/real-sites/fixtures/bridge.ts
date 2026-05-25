import http from "node:http";
import type { AddressInfo } from "node:net";

export type MockBridge = {
  url: string;
  token: string;
  marker: string;
  close: () => Promise<void>;
};

export async function startMockBridge(target: "chatgpt" | "claude"): Promise<MockBridge> {
  const token = `e2e-token-${Date.now()}`;
  const marker = `SAYANE_E2E_MARKER::${target}::${Date.now()}::${Math.random()
    .toString(36)
    .slice(2)}`;

  const server = http.createServer((req, res) => {
    const url = new URL(req.url ?? "/", "http://127.0.0.1");
    const sendJson = (status: number, body: unknown): void => {
      res.writeHead(status, {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Authorization, Content-Type",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Content-Type": "application/json; charset=utf-8",
      });
      res.end(JSON.stringify(body));
    };

    if (req.method === "OPTIONS") {
      sendJson(200, { ok: true });
      return;
    }

    if (url.pathname === "/health") {
      sendJson(200, { ok: true });
      return;
    }

    const auth = req.headers.authorization ?? "";
    if (auth !== `Bearer ${token}`) {
      sendJson(401, { detail: "Unauthorized" });
      return;
    }

    if (url.pathname === "/profiles") {
      sendJson(200, [{ id: "default", name: "E2E User" }]);
      return;
    }

    if (url.pathname === "/context-packet") {
      const requestedTarget = url.searchParams.get("target") ?? target;
      if (requestedTarget === "claude") {
        sendJson(200, {
          target: "claude",
          format: "anthropic_messages",
          payload: {
            system: `Sayane real DOM E2E system context. ${marker}`,
            messages: [
              {
                role: "user",
                content: `Insert-only test. Do not send. ${marker}`,
              },
            ],
          },
        });
        return;
      }
      sendJson(200, {
        target: "chatgpt",
        format: "openai_chat",
        payload: {
          messages: [
            {
              role: "system",
              content: `Sayane real DOM E2E system context. ${marker}`,
            },
            {
              role: "user",
              content: `Insert-only test. Do not send. ${marker}`,
            },
          ],
        },
      });
      return;
    }

    sendJson(404, { detail: `Not found: ${url.pathname}` });
  });

  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve));
  const address = server.address() as AddressInfo;

  return {
    url: `http://127.0.0.1:${address.port}`,
    token,
    marker,
    close: () =>
      new Promise<void>((resolve, reject) => {
        server.close((err) => (err ? reject(err) : resolve()));
      }),
  };
}
