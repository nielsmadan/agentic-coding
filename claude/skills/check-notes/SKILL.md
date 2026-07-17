---
name: check-notes
description: Find information in the user's personal notes vault at ~/wrksp/notes (an Obsidian vault with a hand-maintained index.md map). Use when the user says "check notes", "check my notes", "look in my notes", "find in my notes", "what do my notes say about", "from my notes", or otherwise references information stored in their notes.
---

# Check Notes

Retrieve information from the user's personal Obsidian vault at `~/wrksp/notes` so it can answer the current request or feed the current task — without the user having to tell you the path.

## Instructions

### Step 1: Read the index map
Read `~/wrksp/notes/index.md` first. It is a hand-maintained human-readable map: a **Top-level map** table (`work/`, `home/`, `ai/`, `rpg/`, `docs/`) followed by per-area sections and inventories of scripts/assets/skills. Links use Obsidian syntax — `[text](path)`, and `[text](<path with spaces>)` when the path contains spaces.

Match the user's topic against the table and per-area sections to find the most likely area, directory, or file. Treat the index as a **starting point, not authoritative** — it says so itself, and root-level files are skipped by the maintenance job, so it can be stale.

### Step 2: Navigate to the content
Follow the link that best matches the topic. If it points to:
- **a specific file** → read it.
- **a directory or a per-area `README.md` / `CLAUDE.md`** → read that to narrow down, then read the target file.

Read the actual note files for details rather than trusting the index's one-line summaries.

### Step 3: Fall back to search when the index doesn't pinpoint it
If the index doesn't clearly locate the topic (or the topic isn't mapped), search the vault directly. Use `rg` from `~/wrksp/notes`, excluding noise:

```
rg -il "<keywords>" ~/wrksp/notes --glob '!.git' --glob '!.obsidian' --glob '!.trash' --glob '!ai/runs'
```

Widen or narrow keywords as needed (try synonyms, filenames, headings). Read the top matches.

### Step 4: Use what you find
Extract the relevant information and apply it to the user's request — answer the question, or hand the details to whatever task prompted the lookup. Cite the note path(s) you drew from (e.g. `work/setup/dev-stack.md`) so the user can verify. This skill is **read-only retrieval** — do not edit vault files unless the user explicitly asks.

## Examples

### Example 1: Mapped topic
User says: "check my notes for my dev stack"
Actions:
1. Read `~/wrksp/notes/index.md`; the `work/` section maps setup context to `work/setup/dev-stack.md`.
2. Read `work/setup/dev-stack.md`.
3. Summarize the stack, citing the path.
Result: The user gets the info without naming the file.

### Example 2: Fallback search
User says: "what do my notes say about the award-watch baseline?"
Actions:
1. Read `index.md`; `ai/jobs/award-watch/` is mapped but the exact "baseline" file isn't obvious.
2. `rg -il "baseline" ~/wrksp/notes --glob '!.git' --glob '!ai/runs'` → finds `work/reference/award-baseline.md` and `ai/jobs/award-watch/scripts/build_baseline.py`.
3. Read the top hit and answer.
Result: Located despite the index not pinpointing it.

### Example 3: Feeding a task
User says: "use my notes on the CV build to help me add a new role"
Actions:
1. `index.md` → `work/cv/CLAUDE.md`; read it, then the referenced `experience/` and `profiles/*.json`.
2. Apply the documented conventions to the current task.
Result: The note's conventions drive the work.

## Troubleshooting

### Nothing found in the index or search
**Cause:** Topic uses different terminology than the notes, or lives in a root-level file the index doesn't track.
**Solution:** Try synonyms and likely filenames; `rg` the raw text and also list root-level `*.md` files (`ls ~/wrksp/notes/*.md`). If still nothing, tell the user and ask for a hint (area or keyword).

### Index points somewhere stale or the file moved
**Cause:** `index.md` is hand-maintained and can lag reality.
**Solution:** Fall back to Step 3 search. Trust the filesystem over the index.

### Vault not at ~/wrksp/notes
**Cause:** Path differs on this machine or isn't checked out.
**Solution:** Confirm with `ls ~/wrksp/notes`. If absent, tell the user rather than guessing another location.
