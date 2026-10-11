import { execFile } from "node:child_process";
import { homedir } from "node:os";
import { join } from "node:path";

const STATUS_BIN = join(homedir(), "ac", "bin", "agent-sandbox-status");

interface BeforeAgentStartEvent {
  systemPromptOptions: { sections?: Record<string, string> };
}

interface PiApi {
  on(event: "before_agent_start", handler: (event: BeforeAgentStartEvent) => void): void;
}

function sandboxStatus(): Promise<string | undefined> {
  return new Promise((resolve) => {
    execFile(STATUS_BIN, { timeout: 5000 }, (error, stdout) => {
      resolve(error ? undefined : stdout.trim() || undefined);
    });
  });
}

export default function (pi: PiApi) {
  const note = sandboxStatus();
  pi.on("before_agent_start", async (event) => {
    const text = await note;
    if (!text) return;
    // Pi renders the prompt from these options after its handlers mutate them.
    (event.systemPromptOptions.sections ??= {})["sandbox-status"] = text;
  });
}
