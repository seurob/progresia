import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { join } from "node:path";

const maxAttempts = Number(process.env.PRISMA_GENERATE_ATTEMPTS ?? 3);
const retryDelayMs = Number(process.env.PRISMA_GENERATE_RETRY_MS ?? 750);
const clientPath = join(process.cwd(), "node_modules", ".prisma", "client", "index.js");

for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
  const result = spawnSync("npx", ["prisma", "generate"], {
    cwd: process.cwd(),
    encoding: "utf8",
    shell: process.platform === "win32"
  });

  if (result.status === 0) {
    process.stdout.write(result.stdout);
    process.stderr.write(result.stderr);
    process.exit(0);
  }

  const output = `${result.stdout ?? ""}\n${result.stderr ?? ""}`;
  const isWindowsDllLock =
    process.platform === "win32" &&
    output.includes("EPERM") &&
    output.includes("query_engine-windows.dll.node");

  if (!isWindowsDllLock || attempt === maxAttempts) {
    if (isWindowsDllLock && existsSync(clientPath)) {
      console.warn(
        "Prisma generate hit a Windows DLL lock, but an existing Prisma client is available. Continuing."
      );
      process.exit(0);
    }
    process.stdout.write(result.stdout ?? "");
    process.stderr.write(result.stderr ?? "");
    process.exit(result.status ?? 1);
  }

  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, retryDelayMs);
}
