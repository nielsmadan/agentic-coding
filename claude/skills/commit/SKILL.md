---
name: commit
description: Commit ONLY the changes this session made, never another agent's work in the same checkout. Takes an optional commit message argument; generates a short feat/fix/chore message when blank. Use when the user says "commit", "commit this", "commit my changes", "commit just my/this session's changes", or invokes commit — especially when multiple agents share one working tree.
---

# Commit (session-scoped)

Commit the changes **this session** made — and nothing else. Multiple agents may
share one checkout; a plain `git add -A` / `git add .` would sweep in another
session's work. This skill stages by explicit path, and at hunk granularity when
a file was touched by more than one session.

The argument is the commit message. If blank, generate a short one (see Step 4).

## Instructions

### Step 1: Reconstruct what THIS session changed
Build the set of paths you edited this session from **your own actions** — the
`Write`, `Edit`, `NotebookEdit`, and file-creating `Bash` calls you ran. This is
the source of truth for ownership, not the working tree.

- List every file you created, modified, renamed, or deleted this session.
- If the conversation was summarized and you're unsure, reconstruct from the
  summary + visible history. If you still can't tell which changes are yours,
  do NOT guess wide — jump to Troubleshooting → "Unsure which changes are mine".

### Step 2: See the working-tree state
Run these (read-only) to compare your list against reality:
```
git status --porcelain
git diff --stat            # unstaged
git diff --cached --stat   # anything already staged
```
Anything changed in the tree that is NOT in your Step-1 list belongs to another
session (or the user) — leave it alone.

If files are already staged that you did NOT edit, unstage them first so your
commit stays clean: `git restore --staged <their-file>`.

### Step 3: Stage only your changes
For each path YOU edited, decide file-level vs hunk-level:

- **File only you touched** (its entire current diff is your work) → stage whole:
  ```
  git add <path>              # modified or new
  git rm <path>              # you deleted it
  ```
  New files you created and untracked → `git add <path>`.

- **File you AND another session touched** (its diff contains hunks you didn't
  write) → stage surgically with the helper so foreign hunks stay unstaged:
  ```
  python3 scripts/stage-hunks.py <path> --list      # numbered hunks
  python3 scripts/stage-hunks.py <path> 1 3 4       # stage only yours
  ```
  Identify "yours" by matching each hunk to an edit you actually made. When in
  doubt about a hunk, exclude it — under-committing is recoverable, committing
  someone else's half-finished work is not.

Verify before committing: `git diff --cached` should show your changes and only
yours.

### Step 4: Message
- **Argument given** → use it verbatim as the subject.
- **Blank** → generate a short subject following the user's commit policy:
  - Type is one of `feat` (user-noticeable addition), `fix` (something broken now
    works), or `chore` (everything else). No scopes/parentheses.
  - Format: `type: short description`, lowercase, imperative, no trailing period.
  - Body: omit it, or one short sentence of *what* — never why/how, no essays.

### Step 5: Commit and report (silently)
Commit the staged changes, then give a one-line report — don't ask for
confirmation first (unless Troubleshooting sent you to confirm ownership):
```
git commit -m "feat: add commit skill"
```
Report: files committed + the message, e.g.
`Committed 3 files as "feat: add commit skill" (left 1 file from another session untouched).`

If a pre-commit hook fails, fix the reported problem and retry — never
`--no-verify`. If a hook reformats your staged files, re-stage them (Step 3) and
commit again.

### What NOT to do
- Never `git add -A`, `git add .`, `git add -u`, or `git commit -a`.
- Never stage or commit a file you didn't edit this session.
- Never `git push` (harness-blocked; not this skill's job).
- One commit per invocation. If your session did two clearly unrelated things,
  it's fine to make two commits — but never bundle another session's work in.

## Examples

### Example 1: message given, clean ownership
User: `commit "fix: correct off-by-one in pager"`
Actions:
1. This session edited `src/pager.ts` only.
2. `git status` shows `src/pager.ts` modified plus `src/api.ts` modified — api.ts
   isn't mine, leave it.
3. `git add src/pager.ts`; `git diff --cached` confirms only my change.
4. `git commit -m "fix: correct off-by-one in pager"`.
Result: `Committed 1 file as "fix: correct off-by-one in pager" (left src/api.ts from another session untouched).`

### Example 2: blank message, shared file
User: `commit`
Actions:
1. This session added a helper in `utils.ts` and created `helper.ts`. Another
   session also changed `utils.ts` (added a different function).
2. `git add helper.ts`. For `utils.ts`: `stage-hunks.py utils.ts --list` shows 2
   hunks; hunk 1 is mine, hunk 2 is theirs → `stage-hunks.py utils.ts 1`.
3. `git diff --cached` shows helper.ts + only my utils.ts hunk.
4. No argument → generate `feat: add slugify helper`.
5. `git commit -m "feat: add slugify helper"`.
Result: `Committed 2 files as "feat: add slugify helper" (staged only my hunk of utils.ts).`

## Troubleshooting

### Unsure which changes are mine
**Cause:** Context was summarized, or the tree has changes you can't attribute.
**Solution:** Do not commit wide. List the specific files/hunks you believe are
yours, state which you're unsure about, and ask the user to confirm before
committing. Safety overrides the silent-commit default here.

### `stage-hunks.py` reports "git apply --cached failed"
**Cause:** The working tree shifted between listing and staging, or the hunk
context moved.
**Solution:** Re-run `stage-hunks.py <file> --list` to get fresh hunk numbers,
then retry. If a hunk still won't apply cleanly, stage that file whole only if
its entire diff is yours; otherwise report the conflict to the user.

### Nothing to commit after staging
**Cause:** Your edits were already committed, or another session committed them.
**Solution:** `git log --oneline -5` and `git status` to confirm. If your work is
already in history, say so — don't create an empty commit.

### Pre-commit hook keeps failing
**Cause:** Lint/format/type errors in the staged (or repo-wide) code.
**Solution:** Read all reported errors and fix them (per the repo's Test & Lint
policy — never skip with `--no-verify`), re-stage, and commit again.
