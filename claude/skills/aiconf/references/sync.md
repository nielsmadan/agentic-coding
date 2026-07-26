# Sync ruleset

Read this when an artifact exists on **both** sides and the bytes differ. Missing-on-one-side
cases are handled in SKILL.md step 4 and never reach here.

`$REPO` = the template repo (`~/ac`), `$PROJECT` = the deployed project, `$TYPE` = the
installed template type. The template root is `$REPO/templates/$TYPE/`.

## Contents

- [1. Classify the difference](#1-classify-the-difference)
- [2. Semantic merge](#2-semantic-merge)
- [3. Scope — what is comparable](#3-scope--what-is-comparable)
- [4. Present, confirm, apply](#4-present-confirm-apply)

## 1. Classify the difference

Gather, in **each** repo (template repo and project repo):

- `git status --porcelain -- <path-relative-to-repo>` — uncommitted changes
- `git log -p -n 5 -- <path>` — recent history on that path
- the working-tree-vs-HEAD diff if that side is dirty

Then classify. Use the two current versions **plus** the history — *not* a last-commit
timestamp race:

**One side strictly ahead** — only one side has unique changes since the two last agreed; the
other side's content is an older state of the same thing, with nothing the ahead side lacks.
Covers "uncommitted on one side, clean on the other" and "only one side has commits touching
the path." → **plain push/pull**: sync the behind side toward the ahead side. Direction is
per-artifact; one run may pull one file and push another.

**Both sides diverged** — each side has unique changes the other lacks. Do **not** pick a
winner. Do **not** overwrite either side wholesale. → **semantic merge** (section 2).

**One side has no git history for the path** (brand-new untracked file) → treat as
uncommitted/ahead on that side.

## 2. Semantic merge

When both sides diverged, reconcile by reasoning about *what changed on each side*, not by
stitching text hunks. Read both current working-tree versions and both sides' recent history —
`git log -p` is what tells a deliberate **deletion** apart from the other side's **addition**.
Then produce one reconciled version:

- **template-only addition** / **project-only addition** → keep both (union).
- **both added content on the same topic** → fold into one coherent passage; do **not**
  duplicate the advice.
- **deliberate deletion on one side** → honor the removal. Do not resurrect content the
  history shows was intentionally dropped.
- **genuine contradiction** (the two state opposing things) → you cannot silently pick.
  Surface that specific spot to the user and let them choose; leave the rest merged.

For **`.mcp.json`** (and any JSON artifact) reconcile **structurally**, not as prose: union the
`mcpServers`, and for a server present on both sides combine its keys, flagging only genuinely
conflicting values. Never prose-merge JSON.

A semantic merge is **not a direction** — the reconciled result is written to **both** sides so
they re-converge to an identical state.

## 3. Scope — what is comparable

Filtered by the *template's* shape. Anything the template does not ship is out of scope.

### `.mcp.json`

Walk only the server names present in the **template's** `mcpServers`. Project-only servers are
ignored entirely — do not propose adding them to the template.

### `skills/<name>/`

Only skills the template bundles. Walk files recursively; direction is decided **per file**.
Skills present only in the project are ignored. A file added on only one side of a bundled
skill (e.g. a new `references/foo.md`) is **flagged for explicit confirmation**, not
auto-applied.

### `settings.local.json`

**Skip.** Template entries are union-merged into the project at install, so they are always
present, and arrays have no useful directional diff. If the user wants a template-side refresh,
point them at a mechanical re-install (`deploy.py $TYPE $PROJECT`).

### Instructions snippet

`$REPO/templates/$TYPE/instructions.md` ↔ a passage inside `$PROJECT/CLAUDE.md` **and** a
passage inside `$PROJECT/AGENTS.md`. Treat the two project-side files as **independent** sync
targets — a pull from CLAUDE.md does not auto-overwrite AGENTS.md, and vice versa. Each can
resolve differently (e.g. AGENTS.md a clean pull while CLAUDE.md needs a merge); reconcile each
against the template snippet on its own.

There is **no marker anchor** — install appended the snippet once per file and the user is free
to refactor or integrate it afterwards.

**Locate the project-side passage** (grep-based, in order):

1. Extract the snippet's first markdown heading line (e.g. `## Flutter project tooling`). Grep
   that exact line in the target file. Exactly one match → that is the start.
2. If zero matches, grep for each of the three most distinctive bigrams from the template
   snippet (MCP server names, skill names like `flutter-upgrade`, characteristic compound
   phrases). If exactly one line matches at least two of the three → the earliest match's line
   is the start.
3. Still zero or multiple → ask the user where the snippet lives (line range or heading), or
   whether it was removed intentionally.

**Find the end** from the located start line:

- Read the start line's heading level (count `#`; `##` = level 2).
- The passage ends at the line *before* the next heading whose level is **≤** the start
  heading's level, or at EOF, whichever comes first.
- So the passage = the start heading plus all nested content. Deeper headings are included;
  sibling/parent headings end it.

Before any push, show the full proposed replacement (start line, end line, content) and require
explicit approval. Never auto-write it.

Pull → write `$REPO/templates/$TYPE/instructions.md`. Push → replace the located passage,
preserving everything outside it. Merge → reconcile per section 2, then write the merged
passage into the target file **and** into the template snippet.

**Missing snippet (state-file caveat).** If the snippet is entirely absent from one of the
project's instruction files while the template has one, do NOT one-off push it. Flag it and
recommend the two-step recovery:

1. Edit `$PROJECT/.aiconf/state.json`, removing the missing target from
   `snippet_installed[$TYPE]` (e.g. drop `"AGENTS.md"`), or delete the whole entry to
   re-install both.
2. Re-run the install for that type — it re-appends to the missing target(s) only.

This is the only documented case where the *user* edits `.aiconf/state.json`. The sync path
itself never reads or writes that file — it is install-side state, outside the sync model.

### `.agents/skills/<name>` symlink

Self-heal only, not a directional sync. Install creates `$PROJECT/.agents/skills/<name>` →
`../../.claude/skills/<name>`. If missing or stale, recreate it with the expected target. Skip
silently if that path exists as a real file or directory — never clobber user content. Run this
repair pass after the main scope decisions.

## 4. Present, confirm, apply

Group proposals by file, one outcome label each:

- `←` pull — write into `$REPO/templates/$TYPE/<path>`
- `→` push — write into `$PROJECT/<path>`
- `⇄` merge — write the reconciled result into **both** sides
- `⚠` one-sided, unresolved contradiction, or needs a manual decision

Show each proposal as `diff -u`:

- `←`/`→` → source-vs-destination.
- `⇄` → the reconciled version diffed against **both** current versions, so the user sees
  exactly what each side gains and loses. Call out any contradiction and let them decide it
  before applying.

Then ask: approve all / pick a subset / abort. Apply only what was approved:

- `←`/`→` → overwrite the destination with the source bytes.
- `⇄` → write the reconciled bytes to both paths.

**Never delete files. Never write outside the matched template's scope. Never modify
`settings.local.json` from this path.**

## Edge cases

- **Template repo dirty** with changes unrelated to this sync → fine. Only paths under
  `templates/$TYPE/` are touched, and the user reviews via `git diff` before committing.
- **Project not a git repo** → history-based classification is unavailable on that side. Treat
  the project as uncommitted/ahead and say so explicitly, so the user knows the direction call
  rests on content alone.
