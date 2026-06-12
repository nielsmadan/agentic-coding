---
name: check-claude-projects
description: Search past Claude Code session transcripts under ~/.claude/projects to recover context from earlier work — across the current project AND its sibling checkouts (e.g. wrksp/app/dev1, wrksp/app/dev2). Use when a bug/topic/decision was handled in a previous session but you don't know which session or which checkout folder it lived in, or when the user says "we fixed/discussed this before", "find the session where", "recover prior context", "check claude projects", "search past sessions/transcripts", or "which checkout was that in".
---

# Check Claude Projects

Recover context from a previous Claude Code session by searching its stored
transcripts, then **reading** the relevant session so the current task continues
from where it left off instead of starting from scratch.

Claude Code stores one folder per project under `~/.claude/projects/`, named by
encoding the project's absolute cwd (every non-alphanumeric char → `-`). Each
folder holds `.jsonl` transcripts. The user often checks one repo out into
sibling dirs (`wrksp/app/dev1`, `wrksp/app/dev2`, …) and won't know which
folder a past session lived in — so the search spans siblings by default.

## When to use

Trigger this whenever earlier conversational context would help and you don't
know where it is: a bug resurfaces that was fixed before, a decision was made in
a prior session, "we already looked at this", etc. The goal is for **you** to
read the prior context and use it — not to hand the user a ranked list of hits
unless they ask.

## Instructions

### Step 1: Pick the search query

Choose distinctive keyword(s) tied to the context — an error string, function
name, symbol, ticket id, or unusual phrase. The query is a regex (default
case-insensitive). Prefer a literal distinctive token over generic words.

### Step 2: Run the search

```bash
python3 scripts/search_sessions.py "QUERY" [--cwd DIR] [--scope siblings|current|all] [--app NAME] [--days N]
```

- Default scope is `siblings`: the current project folder plus every sibling
  checkout sharing its parent path (the `wrksp/app/*` case). This is usually
  what you want — run it with no flags first.
- `--app NAME` searches every project folder whose name contains `NAME`
  (e.g. `--app mathfiend`). Use when you know the app but not the checkout, or
  when the current dir sits directly under `$HOME` (then `siblings` over-matches
  every project — the script prints a note when that happens).
- `--scope all` searches every project. Use only as a last resort.
- `--days N` limits to transcripts modified in the last N days ("a week ago").
- `--list-folders` prints the resolved scope without searching — use it to sanity-check
  the folder set before a broad search.

Inspect the script for the full flag list and snippet/context options.

### Step 3: Read the candidate session(s)

The script lists matching sessions newest-first, each with its transcript
`path`, AI `title`, `cwd`, git `branch`, timestamp range, and snippets. Pick the
most likely one (title + recency + branch are strong signals) and **Read the
transcript file at `path`** to absorb the actual prior context — the diagnosis,
the fix, the decision. The `.jsonl` is one JSON record per line; read the user
and assistant `message.content` and any `aiTitle`. Read more than one if the
right session is ambiguous. The per-session `cwd` field is the source of truth
for which checkout a session came from — trust it over the encoded folder name,
which is lossy (see Troubleshooting).

Transcripts can contain secrets or PII that surfaced in earlier sessions (pasted
keys, tool output). Use them as context to do the work — do not echo such values
back to the user or into new files.

### Step 4: Use it

Apply the recovered context to the current task. If the user asked for it,
give a short summary of what the past session found; otherwise just continue the
work informed by it. Cite which session (title + date) you pulled it from so the
user can trace it.

### If nothing matches

Widen progressively: retry with a looser/alternate query → `--app NAME` →
`--scope all` → drop `--days`. Confirm the scope with `--list-folders` if results
seem too narrow.

## Examples

### Example 1: A bug comes back

User: "This keyboard-shortcut crash is back — didn't we fix this a while ago?"

Actions:
1. `python3 scripts/search_sessions.py "KeyboardShortcut" --app juggler`
2. Two sessions match; the newer one is titled "Fix shortcut recorder crash on
   empty binding". Read its transcript at the printed `path`.
3. The prior session shows the fix was guarding `binding == nil` in
   `ShortcutField`. Apply the same guard / confirm it regressed.

Result: "Found it — session 'Fix shortcut recorder crash on empty binding'
(2026-06-03) in `wrksp/juggler/ShortcutField`. The fix was a nil-guard on the
binding; the regression dropped it. Re-applying."

### Example 2: Which checkout had the migration work?

User: "Where did we write the schema migration for mathfiend? Was it dev1 or one
of the others?"

Actions:
1. `python3 scripts/search_sessions.py "migration" --app mathfiend --days 30`
2. Matches land in `wrksp-mathfiend-backend2`. Read that transcript.

Result: "It was in `wrksp/mathfiend/backend2`, session 'Add users table
migration' (2026-05-28)."

## Troubleshooting

### `siblings` matches every project
**Cause:** The `--cwd` sits directly under `$HOME` (e.g. `~/ac`), so its parent
is `$HOME` and the parent-prefix matches all project folders. The script prints
a note when this happens.
**Solution:** Narrow with `--app NAME`, or `--scope current` for just this
project.

### Too many noisy matches
**Cause:** A generic query, or the live current session echoing the query back
in its own transcript.
**Solution:** Use a more distinctive token, add `--days N`, lean on the `title`
field to pick the real session, and ignore the most-recent hit if it's clearly
the current conversation.

### No matches but you're sure it existed
**Cause:** Wrong scope, the phrase wasn't literally in the text, or the work
was in an unexpected checkout.
**Solution:** Try `--list-folders` to confirm scope, switch to `--app NAME` or
`--scope all`, and search a different distinctive term (error code, symbol).

### Folder name doesn't decode cleanly
**Cause:** Encoding is lossy — `/`, `.`, `_` all become `-`, so a folder name
can't be reliably reversed into a path.
**Solution:** Don't decode names; match on the encoded folder name (search by
`--app` substring) and trust the `cwd` field printed from inside each session.

### Siblings scope pulls in folders that aren't really siblings
**Cause:** `siblings` prefix-matches the *encoded* parent path, and encoding is
lossy. A neighbour dir like `b-c`/`b.c`/`b_c` next to parent `b` shares the
encoded prefix and gets swept in; distinct real paths can even collide to the
same folder name.
**Solution:** Treat the extra folders as harmless noise, or narrow with
`--app NAME`. When attributing a session to a checkout, trust its printed `cwd`
field rather than the folder name.
