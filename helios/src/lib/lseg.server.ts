import { type ChildProcessWithoutNullStreams, spawn } from "node:child_process";
import path from "node:path";
import readline from "node:readline";
import type { LsegErr, LsegErrorCode } from "./lseg-types";

const SCRIPT = path.join(process.cwd(), "python", "lseg_bridge.py");

type Pending = {
  resolve: (value: unknown) => void;
  timer: ReturnType<typeof setTimeout>;
};

let child: ChildProcessWithoutNullStreams | null = null;
let reader: readline.Interface | null = null;
let pending: Pending | null = null;
let queue: Promise<unknown> = Promise.resolve();

function err(code: LsegErrorCode, message: string, detail: string | null = null): LsegErr {
  return { ok: false, code, message, detail };
}

function isAbort(error: unknown): boolean {
  if (!error || typeof error !== "object") return false;
  const e = error as { name?: string; code?: string; message?: string };
  return (
    e.name === "AbortError" ||
    e.code === "ABORT_ERR" ||
    e.code === "ECONNRESET" ||
    /aborted|econnreset/i.test(e.message ?? "")
  );
}

function settle(value: unknown) {
  if (!pending) return;
  clearTimeout(pending.timer);
  const { resolve } = pending;
  pending = null;
  resolve(value);
}

function killWorker() {
  const current = child;
  child = null;
  reader = null;
  if (current && !current.killed) {
    current.kill("SIGKILL");
  }
}

function spawnWorker() {
  if (child && !child.killed) return child;
  const proc = spawn("python3", ["-u", SCRIPT, "--loop"], {
    cwd: process.cwd(),
    env: { ...process.env, PYTHONUNBUFFERED: "1" },
    stdio: ["pipe", "pipe", "pipe"],
  });
  child = proc;
  proc.stderr.setEncoding("utf8");
  let stderr = "";
  proc.stderr.on("data", (chunk: string) => {
    stderr += chunk;
    if (stderr.length > 8000) stderr = stderr.slice(-4000);
  });
  proc.stdin.on("error", () => {
    /* EPIPE if python already exited */
  });
  reader = readline.createInterface({ input: proc.stdout });
  reader.on("line", (line) => {
    const text = line.trim();
    if (!text.startsWith("{")) return;
    try {
      settle(JSON.parse(text) as unknown);
    } catch {
      settle(err("upstream", "Python bridge returned unreadable output.", text.slice(0, 500)));
    }
  });
  proc.on("error", (error) => {
    const code = (error as NodeJS.ErrnoException).code;
    if (code === "ENOENT") {
      settle(
        err("library_missing", "Python 3 is not available, so the LSEG desktop bridge cannot run."),
      );
      return;
    }
    settle(err("upstream", error.message));
  });
  proc.on("close", () => {
    if (child === proc) child = null;
    reader = null;
    settle(
      err(
        "workspace_unavailable",
        "LSEG Workspace is not running (or this process cannot reach its desktop proxy).",
        stderr.slice(0, 2000) || null,
      ),
    );
  });
  return proc;
}

function runOne(payload: unknown, timeoutMs: number): Promise<unknown> {
  return new Promise((resolve) => {
    const timer = setTimeout(() => {
      killWorker();
      settle(
        err("upstream", "LSEG request timed out. Try a shorter window or a coarser bar size."),
      );
    }, timeoutMs);
    pending = { resolve, timer };
    try {
      const proc = spawnWorker();
      proc.stdin.write(`${JSON.stringify(payload)}\n`);
    } catch (error) {
      settle(
        err(
          isAbort(error) ? "upstream" : "upstream",
          isAbort(error)
            ? "Fetch was cancelled. Retry the request."
            : error instanceof Error
              ? error.message
              : String(error),
        ),
      );
    }
  });
}

export function runBridge(payload: unknown, timeoutMs = 45000): Promise<unknown> {
  const job = queue.then(
    () => runOne(payload, timeoutMs),
    () => runOne(payload, timeoutMs),
  );
  queue = job.then(
    () => undefined,
    () => undefined,
  );
  return job;
}
