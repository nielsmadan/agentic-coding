---
name: summary
description: Summarize and explain current git changes (staged by default, falling back to unstaged if nothing is staged) in detail, then propose two conventional-commit messages (one detailed, one short). Supports `--quick` for a short recap of the current task and next steps. Use when user says "summary", "summarize staged", "summarize my changes", "explain what I changed", "propose a commit message", "commit summary", "where are we", "what's next", or invokes the summary skill. Read-only — does not commit or stage.
argument-hint: [--quick]
---

# Summary

Explain current git changes in depth, then propose conventional-commit messages. Prefers staged changes; falls back to unstaged if nothing is staged. Analysis only — never runs `git commit`, `git add`, or any state-changing command.

## Modes

- **Default**: detailed per-change writeup + long + short commit messages.
- **`--quick`**: short recap of the task being worked on, what's been done so far, and what's next. No git mechanics (branch, file counts), no commit messages. Use when the user wants to orient themselves mid-session.

If `--quick` is passed, jump to the "Quick mode" section below and skip everything else.

## Instructions

### Step 1: Pick the scope (staged, with unstaged fallback)

Run `git diff --cached --stat`.

- **If non-empty**: scope = staged. Use `git diff --cached` for the rest of the analysis. This is the preferred path — assume the user has curated what they want to commit.
- **If empty**: run `git diff --stat`.
  - **If non-empty**: scope = unstaged. Open the writeup with a one-line note: "Nothing staged — summarizing unstaged changes instead." Use `git diff` for the analysis. Commit messages still apply (the user can stage and commit afterward).
  - **If also empty**: stop. Tell the user "No changes — working tree is clean."

Throughout the rest of the skill, "diff" means whichever scope was selected here.

### Step 2: Read the full diff

Run `git diff --cached` (staged scope) or `git diff` (unstaged scope) — whichever Step 1 selected. For large diffs (hundreds of lines), run the corresponding `--stat` form first to orient, then read the full diff. If the diff is enormous (thousands of lines), summarize per-file rather than trying to hold the whole thing.

Also helpful but optional:
- `git status --short` — flags partially-staged files (both `M` in column 1 and `M` in column 2)
- `git log -1 --format='%s'` — shows the last commit's subject for tone/style reference

### Step 3: Analyze the changes

Classify by nature. For each distinct change, identify:

- **Intent**: choose from exactly three types — `feat`, `fix`, or `chore`. Do **not** use `refactor`, `docs`, `test`, `build`, `ci`, `style`, `perf`, or `revert`; those all fall under `chore`.
  - `feat` — new user-visible capability or behavior change.
  - `fix` — user-visible bug fix.
  - `chore` — anything the user will not notice: refactors, tests, docs, CI, build config, dependency bumps, formatting, tooling, dev-only changes.
  - When in doubt, ask: "would an end user notice this if they ran the new code?" If no, it's `chore`.
- **Scope**: infer from paths (e.g. `api/`, `ui/`, `db/`, `auth/`, top-level package name). Skip scope if changes span many unrelated areas.
- **Key behaviors**: what does the code now do that it didn't before, or vice versa. Name functions/classes/endpoints/flags that changed.
- **Side effects**: new dependencies, config changes, migration SQL, env vars, public API changes, breaking changes.
- **Non-obvious subtleties**: control-flow changes, new error paths, concurrency implications, performance characteristics.

If changes span multiple unrelated intents (e.g. a feat + an unrelated fix), flag that the commit should probably be split.

### Step 4: Present the detailed summary

Structure the output:

```
## What's staged

### <logical change 1>
<2-4 sentences explaining the change, the mechanism, the why if inferrable>

- File: `path/to/file.ext` — <what changed and why it matters>
- File: `path/to/other.ext` — <...>

### <logical change 2>
<...>

## Side effects / things to double-check
- <new dep, migration, breaking change, etc.> — or omit if none
```

Go into real detail — don't just restate filenames. A reader who hasn't seen the diff should understand what the code now does.

### Step 5: Propose two conventional commit messages

Conventional Commits format: `<type>(<optional scope>): <description>`.

Present the **long form first, then the short form**.

**Long form** (use when the change has meaningful context):
- First line: `<type>(<scope>): <description>`, ≤ 72 characters, imperative mood, no trailing period
- Blank line
- Body: wrapped at ~72 chars. Tight — two or three short paragraphs at most, or a single paragraph plus a handful of bullets for genuinely distinct concerns. Explains the *why* and the *mechanism*. Does **not** enumerate files, renames, or line-level changes — those are in the diff.
- Blank line + footer (optional): `BREAKING CHANGE: <desc>`, `Refs: #123`, `Co-authored-by: ...`.

**Body conciseness rules — follow strictly:**
- If a sentence restates what the diff already shows (filenames, renames, "X moved to Y", function lists), cut it.
- One line per concept, not per file. "Every test now hosts a single `@Suite`" stands alone; don't list the 14 files.
- Prefer one sentence over a bullet list when possible. Use bullets only when concerns are genuinely distinct and each needs its own justification.
- Skip the body entirely if the title already says everything and there's no meaningful *why* to add — degrade to the short form.
- Don't repeat the title in the opening sentence.

**Short form** (one-liner, for the shell):
- Same format as the long title: ≤ 72 characters, imperative, no trailing period.

If the commit would be breaking, use `<type>!:` notation in both forms AND include a `BREAKING CHANGE:` footer in the long form.

Format the output:

````
## Proposed commit messages

### Long
```
feat(auth): add refresh-token rotation

Rotate refresh tokens on every use and invalidate the prior
token family on reuse detection. Prevents replay attacks when
a refresh token leaks.

Refs: #482
```

### Short
```
feat(auth): add refresh-token rotation
```
````

End by noting: "To commit, run `git commit -F-` and paste the long message, or use `git commit -m '<short>'`."

## Quick mode (`--quick`)

A recap of what the session is working on — the task, not the git mechanics. The user can see branch/staged/unstaged in their own tooling; don't repeat that here.

### Figure out the task

Draw from these, in order of authority:

1. **The conversation so far** — what has the user been asking for in this session? This is the primary source.
2. **Active plan file** — if there's a plan at `~/.claude/plans/<name>.md` (or the project's `plansDirectory`) whose contents match the session's work, it names the task explicitly.
3. **Recent commits on this branch** (`git log --oneline -20 <branch>..HEAD` or similar) — completed sub-tasks already shipped in this session.
4. **Uncommitted diff** (`git diff`, `git diff --cached`) — last-resort hint at what's in flight when the conversation is ambiguous.

Pick the most specific source that fits. Conversation beats plan beats commits beats diff.

### Present the recap

Three sections:

```
## Task
<one or two sentences naming the goal we're working toward>

## State
<short paragraph: what's been done so far this session, what's in flight right now>

## Next
1. <concrete next step>
2. <concrete next step>
```

Rules:
- Keep each section tight — a sentence or two per block.
- If a specific step just finished and the next thing is unclear, say so in State and set Next to "None — what would you like to do next?"
- Do NOT list branch name, file counts, staged/unstaged totals, or other git metadata — the user doesn't want it.
- Max 3 items in Next. If the plan has more remaining, mention it in State ("4 more steps after these") rather than listing them all.

## Examples

### Example 1: Narrow bugfix

**User**: `/summary`

**Staged**: `src/utils/parseDate.ts` — a one-line change fixing timezone handling.

**Output**:

```
## What's staged

### Fix timezone handling in parseDate
`parseDate(str)` was constructing `new Date(str)` without normalizing to UTC, so any naked ISO date (e.g. "2026-04-23") was interpreted in the user's local timezone and could land on the previous day for negative-offset zones.

- File: `src/utils/parseDate.ts` — append `T00:00:00Z` when input lacks a time component before passing to `Date()`.

## Side effects / things to double-check
None.

## Proposed commit messages

### Long
```
fix(utils): normalize date-only strings to UTC in parseDate

Date-only inputs like "2026-04-23" were parsed in the caller's
local timezone, landing on the previous day for negative-offset
zones. Append a UTC suffix before parsing.

Refs: #712
```

### Short
```
fix(utils): normalize date-only strings to UTC in parseDate
```
```

### Example 2: Feature spanning multiple files

**Staged**: new endpoint, handler, DB migration, test file.

The detailed summary calls out each concern (route, handler logic, migration columns, test coverage) under separate sub-headings, flags the migration as a side effect, and proposes a `feat(api): ...` message in both forms.

### Example 3: Mixed concerns

**Staged**: one refactor + one unrelated bugfix.

Surface this in the summary: "These changes address two unrelated concerns. Consider splitting into two commits (`git reset HEAD <file>` to unstage one, then commit separately)." Still offer proposed messages, but present them as "if you keep the commit as-is" along with separate messages for each concern if the user chooses to split.

### Example 4: Quick mode

**User**: `/summary --quick`

**Context**: session has been adding a `/summary` skill and wiring up a Jina MCP server. An active plan exists at `~/.claude/plans/web-fetching.md`. Skill file is written; just finished refining the `--quick` output format.

**Output**:

```
## Task
Add Jina MCP for web fetching and create a `/summary` skill that explains staged changes and recaps session state.

## State
Jina MCP is live (registered user-level, verified). The `/summary` skill exists with the detailed mode + commit-message output; `--quick` mode was just reworked to focus on task state rather than git mechanics.

## Next
1. Try `/summary --quick` in a fresh session to see how the recap reads.
2. Decide whether other cross-project guidance should move from the project `CLAUDE.md` into the global one.
```

If a task just wrapped up:

```
## Task
Set up Jina MCP server for cleaner web fetches.

## State
Done — key registered, tool verified against a JS-heavy docs page, settings.json permissions added.

## Next
None — what would you like to do next?
```

### Example 5: Conciseness — trim a wordy body

Bodies drift wordy when they enumerate what the diff already shows. Below is the kind of output to avoid, followed by the right version.

**Too wordy** (restates the diff — files, renames, specific moves):

```
chore: reorganize JugglerTests into @Suite structs and topic files

Wrap free @Test functions across 14 test files in @Suite structs so each
test runs on a fresh instance, matching Swift Testing idioms and defending
against shared-state pollution. Split the grab-bag JugglerTests.swift
(889 lines) into topic-focused files. Add shared helpers.

- Every test file now hosts a single @Suite("<Subject>") struct; file-scope
  private helpers moved inside their hosting struct as methods.
- JugglerTests.swift → SessionTests, SessionStateTests, SessionTitleModeTests,
  BeaconTests, HighlightConfigTests, QueueOrderModeTests; TerminalType tests
  folded into the existing TerminalTypeTests.
- New Tags.swift declares integration/slow/flaky tags; IntegrationTests now
  carries .tags(.integration) for future fast/slow-loop filtering.
- New TestSupport.swift holds the shared makeSession helper.
- Cosmetic fixes: HookServer suite renamed from HTTPProtocolAndHookServer,
  Xcode boilerplate banners dropped, filler tag doc removed.
```

**Right** (why + mechanism only; no file lists, no renames):

```
chore: reorganize JugglerTests into @Suite structs and topic files

Each test now runs on a fresh instance, matching Swift Testing
idioms and defending against shared-state pollution. The
grab-bag JugglerTests.swift is split by subject. Introduces
integration/slow/flaky tags for future fast/slow-loop filtering.
```

The cut: file enumerations, rename lists, cosmetic notes, and anything a reader can see in `git show`.

## Troubleshooting

### No changes anywhere

**Cause:** Working tree is clean — nothing staged, nothing unstaged.
**Solution:** Tell the user "No changes — working tree is clean." Don't try to summarize untracked files or recent commits; that's outside this skill's scope.

### Nothing staged but unstaged work exists

**Cause:** User hasn't run `git add` yet, but has edits in the working tree.
**Solution:** Fall back to summarizing unstaged changes (`git diff` instead of `git diff --cached`). Open the writeup with one line acknowledging the fallback: "Nothing staged — summarizing unstaged changes instead." Still propose commit messages; the user can stage and commit afterward.

### Diff is huge (thousands of lines)

**Cause:** Large refactor, generated files, lockfile updates, or accidental checkin.
**Solution:**
1. Use `git diff --cached --stat` to get per-file sizes.
2. Explicitly list files that look auto-generated (lockfiles, build output, snapshots) — note them briefly without summarizing line-by-line.
3. For remaining files, read diffs in chunks per file.
4. If a specific file accounts for most of the diff and looks mechanical (e.g. mass rename), say so instead of listing every change.

### Partially staged files

**Cause:** The file has both staged and unstaged changes.
**Solution:** Note which files are partially staged (from `git status --short`). Analyze only the staged portion. Mention to the user that the unstaged portion exists and isn't covered.

### Cannot determine type unambiguously

**Cause:** Change could reasonably be `feat` or `chore`, or `fix` vs `chore`.
**Solution:** Apply the "user-notices" test — if no end user would notice, it's `chore`. If they would (new capability or visible bug fix), it's `feat` or `fix`. Never use any type outside `feat`/`fix`/`chore`.
