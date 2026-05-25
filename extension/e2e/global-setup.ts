import { execSync, spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";

const EXTENSION_DIR = path.resolve(__dirname, "..");
const SAYANE_ROOT = path.resolve(EXTENSION_DIR, "..");
const E2E_DIR = path.join(EXTENSION_DIR, "e2e");
const ENV_FILE = path.join(E2E_DIR, ".e2e-env.json");
const PID_FILE = path.join(E2E_DIR, ".bridge-pid.json");

export default async function globalSetup(): Promise<void> {
  const e2eHome = fs.mkdtempSync(path.join(os.tmpdir(), "sayane-e2e-home-"));

  execSync("python3 e2e/setup-bridge.py", {
    cwd: EXTENSION_DIR,
    env: {
      ...process.env,
      HOME: e2eHome,
      SAYANE_E2E_ENV_FILE: ENV_FILE,
      PYTHONPATH: path.join(SAYANE_ROOT, "src"),
    },
    stdio: "inherit",
  });

  const bridge = spawn(
    "python3",
    [
      "-m",
      "uvicorn",
      "sayane.bridge.app:create_app",
      "--factory",
      "--host",
      "127.0.0.1",
      "--port",
      "38741",
    ],
    {
      cwd: SAYANE_ROOT,
      env: {
        ...process.env,
        HOME: e2eHome,
        PYTHONPATH: path.join(SAYANE_ROOT, "src"),
      },
      stdio: "ignore",
      detached: true,
    },
  );
  bridge.unref();

  fs.writeFileSync(PID_FILE, JSON.stringify({ pid: bridge.pid, envFile: ENV_FILE }));

  const deadline = Date.now() + 30_000;
  while (Date.now() < deadline) {
    try {
      const res = await fetch("http://127.0.0.1:38741/health");
      if (res.ok) return;
    } catch {
      /* retry */
    }
    await new Promise((r) => setTimeout(r, 250));
  }
  throw new Error("Bridge did not become healthy within 30s");
}
