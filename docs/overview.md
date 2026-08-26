# Docs Overview

Index for the `docs/` tree. **`docs/` is supplementary** — the canonical
current-state documentation for this repo lives in [`AGENTS.md`](../AGENTS.md)
(structure, permissions, project templates, shell config) and
[`README.md`](../README.md) (the top-level entry point).

## What's here

| Doc | Purpose |
|-----|---------|
| [`security-model.md`](security-model.md) | What the sandbox guards against and what it does not, git and `gh` authentication, why `git push` behaves differently in sandboxed, raw, and interactive contexts, and the known gaps. |
| [`skill-best-practices.md`](skill-best-practices.md) | Reference extract of Anthropic's skill-building guide — planning, structure, testing, distribution. A static external reference, not code-derived. |

## Where to look for what

- **How the repo is laid out, how to add a skill / permission / template** →
  [`AGENTS.md`](../AGENTS.md).
- **What the sandbox actually protects, and how to still push from your shell** →
  [`security-model.md`](security-model.md).
- **Per-agent skill catalog** → [`loadout/skills/README.md`](../loadout/skills/README.md).
- **How to build a good skill** → [`skill-best-practices.md`](skill-best-practices.md).

> Note: `docs/tmp/` is gitignored scratch space and is not part of the repo.
