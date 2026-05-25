import fs from "node:fs";
import path from "node:path";

const PID_FILE = path.join(__dirname, ".bridge-pid.json");

export default async function globalTeardown(): Promise<void> {
  if (!fs.existsSync(PID_FILE)) return;
  const { pid } = JSON.parse(fs.readFileSync(PID_FILE, "utf8")) as { pid: number };
  try {
    process.kill(pid, "SIGTERM");
  } catch {
    /* already stopped */
  }
  fs.rmSync(PID_FILE, { force: true });
}
