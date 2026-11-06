import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const STATUS_BIN = join(homedir(), ".local", "bin", "agent-sandbox-status");

function sandboxStatus(): Promise<string | undefined> {
  return new Promise((resolve) => {
    execFile(STATUS_BIN, { timeout: 5000 }, (error, stdout) => {
      resolve(error ? undefined : stdout.trim() || undefined);
    });
  });
}

// The OpenCode 2 loader takes a default export with `id` and `setup`.
export default {
  id: "sandbox-status",

  async setup(ctx: any) {
    const note = await sandboxStatus();
    if (!note) return;
    await ctx.session.hook("context", (event: any) => {
      const system = event.system ?? (event.system = []);
      system.push({ type: "text", text: note });
    });
  },
};
