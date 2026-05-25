---
name: sync-project-config
description: Bidirectional sync between a project's deployed agent config (.mcp.json, .claude/skills/<name>/, CLAUDE.md/AGENTS.md snippets) and its canonical template in ~/ac/templates/<type>/. Decides per-file whether to pull project→template or push template→project from diff + git history. Use when the user runs `aiconf sync` or asks to mirror project changes back to the template, or push template updates into a project with diff review.
argument-hint: [project-dir]
---

# Sync Project Config

Two-way sync between a deployed project's agent config and its source template.

## Usage

```
/sync-project-config          # from a project dir: compare CWD against its template
/sync-project-config <dir>    # from the template repo: compare <dir> against its template
```

These invocation forms are **fixed by the user** — do not infer from CWD heuristics. If the form
doesn't match (e.g., two args, or no-arg from a directory with no `.mcp.json` and no
`.claude/skills/`), ask the user to clarify; do not guess.

## Workflow

### 1. Resolve `$PROJECT` and `$TEMPLATE`

- `$TEMPLATE_REPO` is the directory `~/.airc` resolves to via symlink. Resolve portably with:
  ```
  python3 -c 'import os; print(os.path.dirname(os.path.realpath(os.path.expanduser("~/.airc"))))'
  ```
  (macOS BSD `readlink` doesn't accept `-f`, so avoid `readlink -f`.) Typically `~/ac`.
- `$PROJECT` is the argument if given, else CWD.
- Sanity: `$PROJECT` must contain `.mcp.json` or `.claude/skills/`. If neither, abort and ask.
- If `$PROJECT` resolves to `$TEMPLATE_REPO`, refuse — explain the two invocation forms.

### 2. Infer the project type

List the type directories under `$TEMPLATE_REPO/templates/`. For each, count overlap between:
- Template's `mcpServers` names vs project's `.mcp.json` `mcpServers` names
- Template's `skills/<name>/` dirs vs project's `.claude/skills/<name>/` dirs

Best overlap wins. If tied, or zero overlap, ask the user which type. Call the result `$TYPE`.
The template root is then `$TEMPLATE_REPO/templates/$TYPE/`.

### 3. Decide per-artifact direction (diff + git history)

For each artifact in scope (next section), compute the byte diff between the template's
version and the project's version. If identical → skip. Otherwise:

1. Run in each repo (template repo and project repo):
   - `git status --porcelain -- <path-relative-to-repo>` to detect uncommitted changes
   - `git log -1 --format='%ct %H' -- <path>` to get the file's last-commit timestamp

2. Decide:
   - **Uncommitted on one side, clean on the other** → uncommitted side is authoritative.
     Propose syncing the clean side toward it.
   - **Both clean, different last-commit timestamps** → newer timestamp wins. Propose syncing
     the older side toward the newer.
   - **Both have uncommitted changes** → flag as conflict. Show both diffs (template vs
     project, plus each side's working-tree-vs-HEAD diff). Ask the user to resolve manually.
   - **File on only one side** → flag for explicit confirmation; do not auto-create on the
     other side.
   - **One side has no git history for the file** (e.g., it's a brand-new untracked file) →
     treat as uncommitted on that side.

Direction is per-artifact. A single run may pull one file and push another in the same review.

### 4. Scope (template-shape-filtered)

- **`.mcp.json`** — walk only the server names present in the *template*'s `mcpServers`.
  Project-only servers are ignored entirely; do not propose adding them to the template.
- **`skills/<name>/`** — only skills the template bundles. For each, walk files recursively;
  per-file direction. Skills present only in the project are ignored. Files added on only one
  side of a bundled skill (e.g., a new `references/foo.md`) are flagged for explicit
  confirmation, not auto-applied.
- **`settings.local.json`** — **skip**. Template entries are union-merged into the project on
  install so they're always present, and arrays don't have useful directional diffs. If the
  user wants to refresh `settings.local.json` template-side into a project, recommend
  `aiconf <type> <dir>` (mechanical install).
- **Instructions snippet** — `$TEMPLATE_REPO/templates/$TYPE/instructions.md` ↔ a passage
  inside `$PROJECT/CLAUDE.md` **and** a passage inside `$PROJECT/AGENTS.md`. Treat the two
  project-side files as **independent** sync targets — a pull from CLAUDE.md does not
  auto-overwrite AGENTS.md, and vice versa. **No marker anchor** — the install step appended
  the snippet once per file and the user is free to refactor/integrate afterwards.

  For each of CLAUDE.md and AGENTS.md that exists on the project side:

  **Locate the project-side passage (grep-based, in order):**
  1. Extract the snippet's first markdown heading line (e.g., `## Flutter project tooling`).
     Grep that exact line in the target file. If exactly one match → that's the start.
  2. If zero matches, grep for each of the three most distinctive bigrams from the template
     snippet (e.g., MCP server names, skill names like `flutter-upgrade`, characteristic
     compound phrases). If exactly one line matches at least two of the three → use the line
     of the earliest match as the start.
  3. If still zero or multiple → ask the user where the snippet lives (paste the line range
     or the heading), or whether it has been removed intentionally.

  **Determine the end of the passage** from the located start line:
  - Read the heading level of the start line (count `#` characters; e.g., `##` = level 2).
  - The passage ends at the line *before* the next markdown heading whose level is **≤** the
     start heading's level, OR at end-of-file, whichever comes first.
  - This makes the passage = the start heading plus all of its nested content. Sub-sections
     (deeper headings) are included; sibling/parent headings end it.
  - Before any push, show the user the full proposed replacement (start line, end line, and
     content), and require explicit approval — never auto-write without that confirmation.

  Apply the same diff + git-history direction logic as for `.mcp.json` and `skills/<name>/`,
  per target file independently. Pull → write
  `$TEMPLATE_REPO/templates/$TYPE/instructions.md`. Push → replace the located passage
  inside the target file, preserving everything outside it. If CLAUDE.md and AGENTS.md
  *both* hold a divergent passage and both are newer than the template, surface both diffs
  and let the user pick one to pull (or pull both into the template separately for review).

  **Missing snippet (state-file caveat).** If the snippet is entirely missing from one of
  the project's instruction files and the template has one, do NOT perform a one-off push.
  Flag it and recommend this two-step recovery:
  1. Edit `$PROJECT/.aiconf/state.json` and remove the missing target from
     `snippet_installed[$TYPE]` (e.g. drop `"AGENTS.md"`), or delete the whole entry to
     re-install both targets.
  2. Re-run `aiconf $TYPE $PROJECT` — install will re-append the snippet to the missing
     target(s) only.

  This is the only documented case where the user (not the skill) modifies
  `.aiconf/state.json`. The skill itself does NOT read or write `.aiconf/state.json` —
  that's install-side state and not part of the sync model.

- **`.agents/skills/<name>` symlink** — self-heal only. The deploy step creates a symlink
  at `$PROJECT/.agents/skills/<name>` pointing to `../../.claude/skills/<name>`. If the
  symlink is missing or stale (points elsewhere), recreate it with the expected target.
  Skip silently if `.agents/skills/<name>` exists as a real directory or file — do not
  clobber user-authored content. This is not a sync operation in the diff/direction sense;
  it's a one-line repair pass that runs after the main scope decisions.

### 5. Present, confirm, apply

Group proposals by file with a direction label per item:
- `←` pull (write into `$TEMPLATE_REPO/templates/$TYPE/<path>`)
- `→` push (write into `$PROJECT/<path>`)
- `⚠` conflict / one-sided / needs manual decision

For each diffable item, show `diff -u` output. Then ask: approve all / pick subset / abort.
Apply only approved changes by overwriting the destination file with the source file's bytes.

Never delete files. Never write outside the matched template's scope. Never modify
`settings.local.json` from this skill.

### 6. Hand off to git

After writes, tell the user where to inspect:
- For pulls: `cd $TEMPLATE_REPO && git diff`
- For pushes: `cd $PROJECT && git diff` (or `git status` if the project doesn't track the
  written paths)

Do **not** run `git add`, `git commit`, or any state-mutating git operation yourself — see
the repo's git policy in `CLAUDE.md`.

## Edge cases

- **CWD outside any project**, no arg → abort: "no project here; run from a deployed project
  or pass a project dir from the template repo."
- **Type ambiguous** (e.g., a project that overlaps two types) → present both, ask which one.
- **Project has neither `.mcp.json` nor `.claude/skills/`** → not a deployed project; abort.
- **Template repo dirty** (uncommitted changes unrelated to this sync) → still fine; the skill
  only touches files under `templates/$TYPE/` and the user reviews via `git diff` before
  committing.
