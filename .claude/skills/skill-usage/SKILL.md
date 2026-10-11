---
name: skill-usage
description: Report which skills are used, how often, and by which agent (Claude, Codex, Droid, OpenCode, Pi) by counting real skill invocations in the agents' session logs. Use when asked "which skills do we use", "skill usage", "how often is X used", "which skills are unused / dead", "what should we prune", or to compare skill adoption across agents. Not for recovering a past session's content; use check-agent-logs for that.
---

# Skill Usage

Count skill invocations across every agent's session logs and report usage per skill,
per agent, and who triggered it. The script reuses `check-agent-logs`' log locations
and project scoping, but reads each record's structure instead of matching text, so a
skill merely *mentioned* (a file listing, an edit to `loadout/skills/`) never counts.

## Instructions

### 1. Run the report

```bash
python3 .claude/skills/skill-usage/scripts/skill_usage.py [--days 30] [--claude] [--codex] [--droid] [--opencode] [--pi]
```

- `--days N` sets the window (default 30); `--days 0` is all time.
- No agent flag means all five. Scope defaults to every project; narrow it with
  `--app NAME` (cwd substring) or `--scope current|siblings`.
- `--format json` for anything that post-processes the numbers.
- A full 30-day run over all agents takes about 25 seconds.

### 2. Read the columns correctly

- **sessions** — distinct sessions that loaded the skill. Use this to rank skills; it
  is robust to a skill being re-read or re-selected within one session.
- **invoked** — total loads. **user** / **model** split it: *user* is a typed
  invocation (`/skill`, `$skill`, `/skill:name`, Droid skill selection), *model* is the
  agent loading it on its own or another skill calling it.
- Per-agent columns count **sessions**, not invocations.
- **Unused in this window** lists skills in `loadout/skills/` and this repo's
  `.claude/skills/` with no load in the window. Global skills only; plugin skills
  (superpowers, mouthfeel) appear in the table when used but are never listed unused.

How each agent records a load, and therefore what is counted:

| Agent | user | model |
|---|---|---|
| Claude | "Base directory for this skill" record without a tool id | the same record with `sourceToolUseID` |
| Codex | `<skill><name>…</name>` block from `$skill` | tool call naming an installed `…/skills/X/SKILL.md` |
| Droid | `<skill name="…">` block in a user message | `Skill` tool call |
| Pi | `<skill name="…">` block from `/skill:name` | `read` of an installed `SKILL.md` |
| OpenCode | — | `skill` tool call |

Codex and Pi load skills by reading the file, often in chunks, so their *model* loads
count once per session per skill. Every other load counts each time.

### 3. Drill into one skill

```bash
python3 .claude/skills/skill-usage/scripts/skill_usage.py --skill commit --days 90
```

Lists each invocation with time, `agent:session` ref, trigger, and cwd. Pass a ref to
`check-agent-logs` (`search_agent_logs.py --read AGENT:SESSION_ID`) to see how the skill
was used there.

### 4. Report

Lead with the answer to the user's question (top skills, a skill's trend, the unused
list), then the table or the relevant rows. State the window and any `Incomplete:` or
`Excluded … automated session(s)` line from the header, since both change the totals.

## Examples

### Which skills are dead?

User: "Which of our skills haven't been used in the last two months?"

1. Run `skill_usage.py --days 60`.
2. Report the `Unused in this window` line, grouped by whether each skill is meant to
   be invoked by hand (rare use is expected) or by the model (never loading suggests a
   weak `description:`).

### How does Codex use code-review?

User: "Is code-review actually being used in Codex, or only in Claude?"

1. Run `skill_usage.py --skill code-review --codex --days 30`.
2. Summarize the user/model split and the projects; check one session with
   `check-agent-logs` if the model loads look surprising (in practice `longshot`
   re-reads `code-review` at each milestone).

## Troubleshooting

### A skill name looks foreign or dominates the table

**Cause:** automated runs (evals, demos) load skills hundreds of times. Sessions whose
cwd is under a temp directory or a `.sandbox/` directory are excluded by default; other
automation is not detected.
**Solution:** check its sessions with `--skill NAME`; narrow with `--app` or report the
skill separately. `--include-automation` puts the excluded sessions back.

### An agent's column is empty

**Cause:** no sessions for that agent in the window, or its store is missing (the
header then says `Incomplete: no session store for …`).
**Solution:** widen with `--days 0` before concluding the agent never uses skills.

### Counts look low for Codex or Pi

**Cause:** model loads there are file reads, counted once per session, and a read
through an unusual path (a symlink outside a dot-directory) is not recognized.
**Solution:** treat the `sessions` column as the reliable figure for those agents.
