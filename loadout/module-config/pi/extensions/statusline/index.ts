import type {
  ExtensionAPI,
  ExtensionContext,
} from "@earendil-works/pi-coding-agent";
import {
  stripTerminalSequences,
  truncateToWidth,
  visibleWidth,
} from "@earendil-works/pi-tui";

interface FooterState {
  sandboxed: boolean;
  model: string;
  effort: string;
  contextPercent: number | null | undefined;
  statuses: ReadonlyMap<string, string>;
}

const color = (code: string, text: string): string =>
  `\x1b[${code}m${text}\x1b[0m`;
const plain = (text: string): string =>
  stripTerminalSequences(text).replace(/\s+/gu, " ").trim();
const separator = color("2", " │ ");

function contextSegment(percent: FooterState["contextPercent"]): string {
  if (percent == null || !Number.isFinite(percent))
    return `🧠 ${color("2", "?")}`;
  const pct = Math.max(0, Math.floor(percent));
  const filled = Math.min(10, Math.floor(pct / 10));
  const shade = pct >= 90 ? 167 : pct >= 70 ? 173 : pct >= 45 ? 179 : 108;
  return `🧠 ${color(`38;5;${shade}`, "▓".repeat(filled))}${color("2", "░".repeat(10 - filled))}${color(`38;5;${shade}`, ` ${pct}%`)}`;
}

export function renderFooter(width: number, state: FooterState): string[] {
  if (width <= 0) return [];
  const model = plain(state.model)
    .replace(/^claude-/i, "")
    .toLowerCase()
    .replaceAll(" ", "");
  const effort = plain(state.effort);
  const segments = [
    {
      priority: 100,
      text: `PI ${color(state.sandboxed ? "32" : "31", state.sandboxed ? "🔒" : "🥩")}`,
    },
    {
      priority: 60,
      text:
        color("33", `🤖 ${model}`) + (effort ? ` ${color("35", effort)}` : ""),
    },
    { priority: 80, text: contextSegment(state.contextPercent) },
    ...Array.from(state.statuses)
      .filter(([key, text]) => key !== "nono" && plain(text))
      .map(([, text]) => ({ priority: 40, text: plain(text) })),
  ];
  while (
    visibleWidth(segments.map(({ text }) => text).join(separator)) > width &&
    segments.length > 1
  ) {
    const lowest = Math.min(...segments.map(({ priority }) => priority));
    segments.splice(
      segments.findLastIndex(({ priority }) => priority === lowest),
      1,
    );
  }
  return [
    truncateToWidth(
      segments.map(({ text }) => text).join(separator),
      width,
      "",
    ),
  ];
}

export default function (pi: ExtensionAPI) {
  const sandboxed = Boolean(
    process.env.AGENT_SANDBOX || process.env.NONO_CAP_FILE,
  );
  let requestRender: (() => void) | undefined;
  const install = (ctx: ExtensionContext) => {
    if (!ctx.hasUI) return;
    ctx.ui.setFooter((tui, _theme, footerData) => {
      requestRender = () => tui.requestRender();
      return {
        invalidate() {},
        dispose() {
          requestRender = undefined;
        },
        render: (width: number) =>
          renderFooter(width, {
            sandboxed,
            model: ctx.model?.id ?? "unknown",
            effort: pi.getThinkingLevel(),
            contextPercent: ctx.getContextUsage()?.percent,
            statuses: footerData.getExtensionStatuses(),
          }),
      };
    });
  };
  pi.on("session_start", (_event, ctx) => install(ctx));
  pi.on("session_tree", (_event, ctx) => install(ctx));
  pi.on("model_select", () => requestRender?.());
  pi.on("thinking_level_select", () => requestRender?.());
}
