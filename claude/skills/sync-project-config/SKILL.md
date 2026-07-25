---
name: sync-project-config
description: Bidirectional sync between a project's deployed agent config (.mcp.json, .claude/skills/<name>/, CLAUDE.md/AGENTS.md snippets) and its canonical template in ~/ac/templates/<type>/. Decides per-file whether to pull project→template, push template→project, or — when both sides diverged — semantically merge them, from diff + git history. Use when the user runs `aiconf sync` or asks to mirror project changes back to the template, or push template updates into a project with diff review.
argument-hint: '[project-dir]'
effort: high
---

# Sync Project Config

Two-way sync between a deployed project's agent config and its source template. Per artifact
it pulls, pushes, or — when both sides have diverged — semantically merges the two.

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

### 3. Decide per-artifact outcome (diff + git history)

For each artifact in scope (next section), compute the byte diff between the template's
version and the project's version. If identical → skip. Otherwise gather, in each repo
(template repo and project repo):
- `git status --porcelain -- <path-relative-to-repo>` to detect uncommitted changes
- `git log -p -n 5 -- <path>` for recent change history on that path
- the working-tree-vs-HEAD diff if the side is dirty

**First classify whether this is a one-sided update or a genuine divergence.** Use the two
current versions plus the history above — *not* a last-commit-timestamp race:

- **One side strictly ahead** — only one side has unique changes since the two last agreed;
  the other side's content is an older state of the same thing, with nothing the ahead side
  lacks. This covers "uncommitted on one side, clean on the other" and "only one side has
  commits/edits touching the path." → **plain push/pull**: propose syncing the unchanged
  (behind) side toward the ahead side. Direction is per-artifact; a single run may pull one
  file and push another.

- **Both sides diverged** — each side has unique changes the other lacks (formerly the
  "newer timestamp wins" and "both uncommitted → bail" cases). Do **not** pick a winner and
  do **not** overwrite one side wholesale. → **semantic merge** (next).

- **File on only one side** → flag for explicit confirmation; do not auto-create on the
  other side.

- **One side has no git history for the file** (e.g., a brand-new untracked file) → treat
  as uncommitted/ahead on that side.

#### Semantic merge (genuine divergence)

When both sides diverged, reconcile them by reasoning about *what changed on each side*,
not by stitching text hunks. Read both current working-tree versions and both sides'
recent history (the `git log -p` above tells deliberate **deletions** apart from the other
side's **additions**). Then produce a single reconciled version:

- **template-only addition** / **project-only addition** → keep both (union).
- **both added content on the same topic** → fold into one coherent passage; do **not**
  duplicate the advice.
- **deliberate deletion on one side** → honor the removal; do not resurrect content the
  history shows was intentionally dropped.
- **genuine contradiction** (the two state opposing things) → you cannot silently pick.
  Surface that specific spot to the user and let them choose; leave the rest merged.

For **`.mcp.json`** (and any JSON artifact) reconcile **structurally**, not as prose: union
the `mcpServers`, and for a server present on both sides combine its keys, flagging only
genuinely conflicting values. Do not prose-merge JSON.

A semantic merge is **not a direction** — the reconciled result is written to **both** the
template and the project so they re-converge to an identical state. See step 5.

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

  Apply the same diff + git-history outcome logic as for `.mcp.json` and `skills/<name>/`,
  per target file independently. Pull → write
  `$TEMPLATE_REPO/templates/$TYPE/instructions.md`. Push → replace the located passage
  inside the target file, preserving everything outside it. **Merge** (the passage and the
  template snippet diverged) → reconcile semantically per step 3, then write the merged
  passage back into the located target-file passage **and** into the template snippet.
  Because CLAUDE.md and AGENTS.md are independent targets, each can resolve differently
  (e.g. AGENTS.md a clean pull while CLAUDE.md needs a merge); reconcile each against the
  template snippet on its own.

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

Group proposals by file with an outcome label per item:
- `←` pull (write into `$TEMPLATE_REPO/templates/$TYPE/<path>`)
- `→` push (write into `$PROJECT/<path>`)
- `⇄` merge (write the reconciled result into **both** sides — see step 3's semantic merge)
- `⚠` one-sided / unresolved contradiction / needs manual decision

For each item, show the proposal as `diff -u`:
- For `←`/`→`, the diff is source-vs-destination.
- For `⇄`, show the reconciled version diffed against **both** current versions (template
  and project), so the user sees exactly what each side gains and loses. Call out any spot
  flagged as a contradiction and let the user decide it before applying.

Then ask: approve all / pick subset / abort. Apply only approved changes:
- `←`/`→` → overwrite the destination file with the source file's bytes.
- `⇄` → write the reconciled bytes to both the template and the project path.

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
