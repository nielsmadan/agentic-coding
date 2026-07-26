---
name: aiconf
description: Set up or sync a project's agent config against its canonical template in ~/ac/templates. Checks whether the project is configured; if not, detects the project type (flutter, react-native, web, railway), confirms, and installs it; if it is, compares every deployed artifact (.mcp.json, bundled skills, CLAUDE.md and AGENTS.md snippets) against the template and reconciles drift per file — pull, push, or semantic merge. Use when the user runs `aiconf`, `aiconf sync`, `aiconf flutter`, or invokes aiconf; or asks to "set up project config", "configure this project", "is this project configured", "install the template", "sync with the template", "mirror project changes back to the template", or "push template updates into a project".
argument-hint: '[type|sync] [project-dir]'
effort: high
---

# aiconf

Single entry point for project-template config. Assess the project, then route:
**not configured** → detect type, confirm, install. **configured** → compare against the
template and reconcile drift.

## Invocation

```
aiconf                  # assess CWD, route
aiconf <dir>            # assess <dir>, route
aiconf sync [dir]       # skip detection, go straight to the sync path
aiconf <type> [dir]     # skip detection, install <type> (still confirms before writing)
```

An argument that names a directory is `$PROJECT`. An argument matching a template type
name is `$TYPE`. `sync` is a keyword. Anything else → ask; do not guess.

## Workflow

### 1. Resolve paths

`$REPO` is the directory `~/.airc` resolves to via symlink:

```
python3 -c 'import os; print(os.path.dirname(os.path.realpath(os.path.expanduser("~/.airc"))))'
```

(macOS BSD `readlink` has no `-f` — do not use it.) Typically `~/ac`.

`$PROJECT` is the directory argument if given, else CWD. If `$PROJECT` resolves to `$REPO`,
refuse — `$REPO` is the template source, not a deployable target; ask for a project dir.

Available types = the directories under `$REPO/templates/` (currently `flutter`,
`react-native`, `web`, `railway`). Read this from disk; never hardcode the list.

### 2. Assess what is installed

A project may have **several types installed** — they compose (e.g. `railway` is a deploy
target that stacks on a `web` project). Build the installed set from three signals, strongest
first:

1. **`$PROJECT/.aiconf/state.json`** → `snippet_installed` keys name types explicitly.
   Definitive when present. Note: a type whose template has no `instructions.md`
   (e.g. `railway`) never appears here even when fully installed.
2. **Deployed skills** — `$PROJECT/.claude/skills/<name>/` matching a
   `$REPO/templates/<type>/skills/<name>/`. The primary signal for skills-only templates.
3. **MCP servers** — `$PROJECT/.mcp.json` `mcpServers` names matching a template's. Weak:
   `react-native` ships an empty map and `web`/`railway` ship no `.mcp.json` at all.

Report the assessment before doing anything, then route:

- **No type installed** → step 3 (configure).
- **One or more installed** → step 4 (sync each installed type).
- **Installed, and another type also looks applicable** → do both: sync what is installed,
  and offer the additional type as a step-3 install. Ask before installing the extra.

### 3. Configure (not yet installed)

**Detect** candidate types from project files. Markers:

| Type | Markers |
|------|---------|
| `flutter` | `pubspec.yaml` (with a `flutter:` dependency), `lib/main.dart`, `ios/Runner/`, `android/app/` |
| `react-native` | `package.json` depending on `react-native` or `expo`; `metro.config.js`, `app.json` with an `expo` key |
| `web` | `package.json` depending on a web framework (`next`, `vite`, `astro`, `svelte`, `remix`, `react-dom` without `react-native`); `index.html`, `app/`, `src/routes/` |
| `railway` | `railway.json`, `railway.toml`, `.railway/`, or a Railway service referenced in CI/deploy config |

`railway` is **additive** — propose it alongside `web`/`react-native`, never instead of.
`flutter` and `react-native` are mutually exclusive; if both match, ask.

**Confirm before writing.** Show the detected type, the evidence, and exactly what install
will do — read the template dir to enumerate it, do not assume:

```
not configured.

  detected: flutter
  evidence: pubspec.yaml (flutter: sdk), lib/main.dart, ios/Runner/

  aiconf flutter will:
    merge  .mcp.json                     +ios-sim, +dart-mcp, +android
    merge  .claude/settings.local.json
    copy   .claude/skills/flutter-upgrade/  (+ .agents/skills symlink)
    append CLAUDE.md, AGENTS.md          instructions snippet (append-once)

proceed?
```

Call out that the snippet append is **append-once and awkward to unwind** (backing it out
needs a `.aiconf/state.json` edit plus deleting the appended passage by hand), so a wrong
type costs real cleanup. If detection is ambiguous or finds nothing, list the available
types and ask — never guess.

**On approval**, run the mechanical installer:

```
python3 "$REPO/templates/deploy.py" <type> "$PROJECT"
```

Then relay its per-artifact output. Remind the user to add `.aiconf/` and
`.claude/settings.local.json` to the project's `.gitignore` if absent.

### 4. Sync (already installed)

For each installed type, compare the project against `$REPO/templates/<type>/` and reconcile.
There is no version stamp anywhere — **"in sync" means the bytes match**.

Three distinct outcomes, and they need different tools:

- **Missing entirely on the project side** (template gained a skill or MCP server since
  install) → this is a *mechanical, additive* gap. Re-running `deploy.py <type> "$PROJECT"`
  is the correct fix; propose it rather than hand-copying.
- **Present on both sides, bytes differ** → a directional or merge decision.
  **Read `references/sync.md`** and follow it. That file holds the full ruleset: how to tell
  a one-sided update from a genuine divergence using git history, how to semantically merge
  when both sides moved, how to locate the instructions snippet inside CLAUDE.md/AGENTS.md
  without a marker anchor, and what is deliberately out of scope.
- **Present in the project, gone from the template** → `deploy.py` is additive and can never
  remove. **Flag only.** Never delete from either side; let the user decide.

Report a per-artifact status table first, then act only on what needs action:

```
react-native: installed
  .mcp.json                        in sync
  .claude/skills/rn-upgrade/       2 files differ      -> see sync.md
  .claude/skills/rn-perf/          missing in project  -> deploy.py (additive)
  CLAUDE.md snippet                diverged both sides -> semantic merge
  AGENTS.md snippet                in sync
  .agents/skills/rn-upgrade        symlink ok
```

If everything matches, say so and stop — no action is a valid outcome.

### 5. Hand off to git

Never run `git add`, `git commit`, or any state-mutating git command — see the repo's git
policy. After writes, point the user at `cd $REPO && git diff` for pulls and
`cd $PROJECT && git diff` for pushes.

## Examples

### Fresh Flutter project, never configured

User runs `aiconf` in `~/wrksp/newapp`.

1. Resolve `$REPO` → `/Users/nielsmadan/ac`; `$PROJECT` → `~/wrksp/newapp`.
2. Assess: no `.aiconf/state.json`, no `.claude/skills/`, no `.mcp.json` → nothing installed.
3. Detect: `pubspec.yaml` with a `flutter:` SDK dep + `lib/main.dart` → `flutter`.
4. Present the plan above; user approves.
5. Run `deploy.py flutter ~/wrksp/newapp`; relay output; note `.aiconf/` should be gitignored.

### Installed project that has drifted

User runs `aiconf sync` in `~/wrksp/flowlab/dev1`.

1. Assess: `state.json` shows `snippet_installed: {react-native: [CLAUDE.md, AGENTS.md]}`,
   and `.claude/skills/rn-upgrade/` exists → `react-native` installed.
2. Compare each artifact. `rn-upgrade/SKILL.md` differs; the CLAUDE.md passage differs.
3. Read `references/sync.md`. Git history shows `rn-upgrade/SKILL.md` changed only in the
   project → **pull** into the template. The CLAUDE.md passage changed on *both* sides →
   **semantic merge**, written to both.
4. Show each proposal as a `diff -u`; user approves a subset; apply only those.
5. Point at `git diff` in both repos.

### Already in sync

User runs `aiconf` in a configured project. Assessment shows every artifact matching.
Report the status table and stop. Do not invent work.

## Troubleshooting

### `$PROJECT` resolves to the template repo

**Cause:** ran bare `aiconf` from inside `~/ac`.
**Solution:** Refuse and ask for a target: `aiconf sync /path/to/project`. The repo is the
source of templates, not a deployment target.

### Type is ambiguous — two types match

**Cause:** `railway` overlapping a `web` project, or a monorepo with both a Flutter and a
web app.
**Solution:** `railway` composes — propose installing it *in addition*. For genuinely
exclusive types (`flutter` vs `react-native`), present the evidence for each and ask. Never
install both to hedge.

### Instructions snippet missing from CLAUDE.md or AGENTS.md

**Cause:** the file was rewritten and the passage dropped, but `state.json` still records it
as installed, so `deploy.py` skips it.
**Solution:** Do NOT hand-push the snippet. Have the user remove the target from
`snippet_installed[<type>]` in `$PROJECT/.aiconf/state.json`, then re-run install for that
type — it re-appends to the missing target only. This is the one case where the user edits
`state.json` directly.

### Template dropped an artifact the project still has

**Cause:** `deploy.py` union-merges and never removes, so a retired MCP server or skill
lingers in the project forever.
**Solution:** Flag it with the evidence; ask before removing anything. This skill never
deletes project files on its own.
