import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const STATUS_BIN = join(homedir(), "ac", "bin", "agent-sandbox-status");

function sandboxStatus(): Promise<string | undefined> {
  return new Promise((resolve) => {
    execFile(STATUS_BIN, { timeout: 5000 }, (error, stdout) => {
      resolve(error ? undefined : stdout.trim() || undefined);
    });
  });
}

export const SandboxStatusPlugin = async () => {
  const note = await sandboxStatus();
  return {
    "experimental.chat.system.transform": async (
      _input: unknown,
      output: { system: string[] },
    ) => {
      if (note) output.system.push(note);
    },
  };
};
