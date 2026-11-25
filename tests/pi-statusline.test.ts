import { expect, test } from "bun:test";
import { stripTerminalSequences, visibleWidth } from "@earendil-works/pi-tui";
import { renderFooter } from "../loadout/module-config/pi/extensions/statusline/index";

const state = {
  sandboxed: true,
  model: "gpt-6-astra",
  effort: "high",
  contextPercent: 5.7,
  statuses: new Map([["nono", "nono sandbox"]]),
};

test("shows the Pi label, sandbox icon, model and context on one line", () => {
  expect(renderFooter(100, state).map(stripTerminalSequences)).toEqual([
    "PI 🔒 │ 🤖 gpt-6-astra high │ 🧠 ░░░░░░░░░░ 5%",
  ]);
});

test("shows raw mode and keeps other extension statuses inline", () => {
  expect(
    renderFooter(100, {
      ...state,
      sandboxed: false,
      statuses: new Map([["plan-mode", "📝 planning\nstep 2"]]),
    }).map(stripTerminalSequences),
  ).toEqual([
    "PI 🥩 │ 🤖 gpt-6-astra high │ 🧠 ░░░░░░░░░░ 5% │ 📝 planning step 2",
  ]);
});

test("unknown context stays unknown and full context fills the bar", () => {
  expect(
    renderFooter(100, { ...state, contextPercent: null }).map(
      stripTerminalSequences,
    ),
  ).toEqual(["PI 🔒 │ 🤖 gpt-6-astra high │ 🧠 ?"]);
  expect(
    renderFooter(100, { ...state, contextPercent: 100 }).map(
      stripTerminalSequences,
    ),
  ).toEqual(["PI 🔒 │ 🤖 gpt-6-astra high │ 🧠 ▓▓▓▓▓▓▓▓▓▓ 100%"]);
});

test("narrow terminals retain the label, sandbox and context before the model", () => {
  expect(renderFooter(26, state).map(stripTerminalSequences)).toEqual([
    "PI 🔒 │ 🧠 ░░░░░░░░░░ 5%",
  ]);
  expect(renderFooter(5, state).map(stripTerminalSequences)).toEqual(["PI 🔒"]);
  expect(renderFooter(2, state).map(stripTerminalSequences)).toEqual(["PI"]);
  expect(renderFooter(0, state)).toEqual([]);
  for (let width = 1; width <= 120; width++) {
    const lines = renderFooter(width, {
      ...state,
      model: "very-long-model-name-".repeat(20),
      statuses: new Map([["task", "長い状態 ".repeat(20)]]),
    });
    expect(lines).toHaveLength(1);
    expect(visibleWidth(lines[0]!)).toBeLessThanOrEqual(width);
  }
});
