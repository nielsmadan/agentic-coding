---
name: doc
description: "Assess documentation state and run the right action (default, no args): survey what exists, find gaps / staleness / quality issues, then route into generate, update, or review. Explicit modes: review (--review), update (--update), generate (--generate <target>), harvest a session log (--session). Scope --staged, --all, or context. Use when unsure what the docs need, or for doc creation, freshness, and quality."
argument-hint: "[ (no args = assess) | --review | --update | --generate <target> | --session --md <file>] [--staged | --all]"
---

# Doc

Assess, review, update, and generate documentation following consistent principles.

## Modes

All modes share one engine — *compare the docs against the current code
reality* — and differ only in what they do with the result:

| Mode | Intent | Writes? | Default scope |
|------|--------|---------|---------------|
| **(no args) — assess** | Survey docs state, propose & run an action plan | No → plan, then runs your picks | whole docs tree + key source |
| `--review [target]` | Assess accuracy / completeness / quality | No → findings, then interactive apply | context (or `<target>`) |
| `--update [target]` | Sync existing docs to current code | Yes — in place, replace stale parts | staged code, falling back to unstaged |
| `--generate <target>` | Create docs that don't exist yet | Yes — new files | the target |

**Assess is the default.** Use it when you don't know what the docs need — it
surveys, classifies, and routes into the three modes below. `--review` and
`--update` are the same comparison (review reports and lets you pick what to
apply; update applies directly from a diff); `--generate` is for greenfield.

## Usage

```
/doc                              # Assess docs state, propose an action plan, run your picks (default)
/doc --staged                     # Assess, but scoped to what staged changes touch
/doc --review payments            # Review docs for a feature, then pick fixes to apply
/doc --review --all               # Review all docs (parallel agents)
/doc --update                     # Sync docs for staged code changes (end of a feature)
/doc --update auth flow           # Sync all docs for a feature/area
/doc --generate <target>          # Generate docs for file/module/feature
/doc --generate --staged          # Generate docs for staged code changes
/doc --generate --unpushed        # Generate docs for code changed across unpushed commits
```

## Documentation Principles

All modes follow these. Review checks conformance; update and generate apply them.

### 1. No Local Paths
- ❌ `/Users/name/projects/app`, `mathfiend/app2`
- ✅ `lib/services/`, `docs/tech/`

### 2. Assume Senior Developer
- Don't explain basic concepts (the framework, the language, etc.)
- Focus on project-specific patterns and WHY decisions were made
- Skip tutorials - show implementation directly

### 3. Single Source of Truth — link to code, don't restate it
- **Code is canonical for signatures.** Reference functions/methods by `file:line`;
  do not paste signatures into prose (they drift the moment the code changes). Prose
  carries only what the agent can't derive by reading the source.
- Same topic at different depths/audiences = OK (overview vs deep dive).
- Identical text copy-pasted across files = NOT OK — link to the canonical doc.

### 4. Separate current-state from why
- **Current state** ("how it works now") is what `--update` keeps in sync as code
  changes. Make it the bulk of the doc.
- **Why** (decisions/rationale) changes rarely — keep it short and distinct, so a
  sync touches the volatile part and leaves the rationale alone. Omit if there's none.

### 5. Index Every Section
- The repo root has `docs/overview.md` mapping the tree (the entry index).
- Each `docs/` subdirectory has `overview.md`: high-level concepts + links to detail.
- Answers: "What's in here and which doc do I need?"

### 6. Document Gotchas
- Non-obvious behavior, common mistakes, platform quirks, things that seem like they
  should work but don't.

### 7. Concrete Examples & Agent-Optimized Writing
- Reference real implementations: `lib/services/foo.dart:123`.
- Clear, factual, active voice; short sentences; bullets over paragraphs.
- For files longer than ~100 lines, add a table of contents at the top.

---

## Gotchas
- `--update`/`--generate --staged` document uncommitted code that may change in
  review. If the code is revised but the docs are committed alongside, they drift.
- `--all` scope includes CLAUDE.md — the skill may propose edits to the project
  instructions file that governs its own behavior.
- `docs/explain/` (the `explain` skill) and `docs/product/` (the `review-product`
  skill) are owned elsewhere and not code-derived. `doc` leaves them alone: exclude
  them from `--all` and never sync them to code. `docs/prd/` *is* `doc`'s — the
  product-behavior layer it keeps in sync with the implementation.

## Assess Mode (default)

The no-args entry point. Use it when you don't know what the docs need: it
surveys the current state, classifies what's required, hands you a prioritized
action plan, then runs the parts you choose by delegating to the other modes.
It never writes without your go-ahead — the plan comes first.

### Workflow

1. **Survey the landscape.** Establish what exists:
   - `docs/` present? Root `docs/overview.md`? Per-subdir `overview.md`?
     `README.md`? A `## Documentation` note in `CLAUDE.md`/`AGENTS.md`?
   - Glob `docs/**/*.md` (exclude `docs/explain/`, `docs/product/` — owned
     elsewhere); note the count and tree.
   - Sketch the code surface worth documenting: top-level modules, features,
     services, APIs.
   - For a large tree (>~15 docs or a big codebase), fan out — one sub-agent per
     check in step 2 — and merge.

2. **Classify the situation:**
   - **No docs (or only a stub):** greenfield. Don't propose documenting
     everything — pick a starter set (root `overview.md` + the few
     highest-value modules) and route those to **Generate**.
   - **Docs exist:** run the three checks that map to the three actions:
     - **Gaps → Generate.** Key source areas with no doc; a missing root or
       subdir `overview.md`.
     - **Staleness → Update.** Docs whose code changed after the doc was last
       touched (`git log -1 --format=%cd -- <doc>` vs recent commits to the code
       it covers), and docs referencing files / `file:line` / symbols that no
       longer exist.
     - **Quality → Review.** A light principles pass: local paths, restated
       signatures, verbatim duplication, placeholders/TODOs, missing required
       sections.

3. **Report state + action plan.** One categorized, sequentially-numbered list:
   ```markdown
   ## Docs Assessment: {repo/scope}
   State: {N docs · overview index present/missing · last synced ~when}

   ### Generate (missing)
   1. {area} — no doc; {why it matters}

   ### Update (stale)
   2. {doc} — {code changed / broken ref}

   ### Review (quality)
   3. {doc} — {issue}

   ### Healthy
   - {what's already fine — so the user knows it was checked}
   ```
   Number findings sequentially across all tiers so the user can select by number.

4. **Offer to execute.** Ask which to run (numbers, `all`, or `none`;
   multi-select where supported). Each selection runs the matching mode's logic
   from this skill — **Generate** / **Update** / **Review** — on that target.
   `none` → stop. Nothing is written without a selection.

### Scope

Defaults to the whole docs tree + key source. To bias toward recent work, add
`--staged` / `--unpushed` (assess only what those changes touch) or a `<target>`
(assess one feature/area).

---

## Session Mode (`--session`)

**Invocation:** `/doc --session --md <conversation.md> [--report <file>]`

Integrate the durable knowledge from one work session into the project's docs. The
input `--md` file is a rendered conversation (plain markdown of USER/ASSISTANT turns)
— you do NOT read Claude Code `.jsonl` files here.

Extract and place three kinds of knowledge, using the SAME layout and conventions as
`--update`/`--generate`:

1. **Gotchas** — pitfalls, surprises, "things we ran into" → the `## Gotchas` section of
   the most relevant module/feature doc.
2. **Decision rationale** — why a product/tech decision was made → the `## Why` section.
3. **Behavior changes** — what the session actually changed → refresh the affected
   `## How it works (current state)` sections.

### Rules

- Find the right target docs via `docs/overview.md` and the existing tree. Prefer
  augmenting existing docs over creating new ones.
- **Never touch `docs/product/`** (owned by `review-product`).
- Only record durable, project-specific knowledge — skip transient chatter and
  anything already documented. It is fine to conclude there is nothing worth adding.
- **Preview** the proposed edits to the user and apply on confirmation. Leave changes
  **uncommitted** (the user commits).
- **Fallback:** if the repo has no `docs/`, write a single `docs/session-harvests/<name>.md`
  (derive `<name>` from the md filename) capturing the same three categories.
- **Report:** if `--report <file>` is given, write the list of doc files you created or
  edited to it, one path per line (repo-relative). If nothing was integrated, write an
  empty file. This is how the caller records what was harvested.

---

## Review Mode (`--review`)

Default mode. Assesses docs against the principles, then offers to apply fixes.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Find docs related to recent conversation |
| `<target>` | A feature/area as a whole | Find all docs covering that feature |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--unpushed` | .md files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` (excluding `docs/explain/`, `docs/product/`) + `README.md` + `CLAUDE.md` |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.

### Workflow

1. **Get file list** based on scope.
2. **Review** (directly if ≤5 files, parallel sub-agents if more), checking each doc
   against the current code — prioritize accuracy/completeness/staleness over prose.
3. **Report findings** by priority (see Output Format). For `docs/prd/` docs, report
   divergences between the PRD and the implementation in **both directions** (doc
   describes behavior the code lacks; code has behavior the doc omits) without assuming
   either side is correct — the user reconciles. This is the implementation side of the
   three-layer check; `review-product` checks `docs/prd/` ↔ `docs/product/`.
4. **Offer to apply.** Present the findings as a numbered list and ask the user which
   to apply — accept multiple selections. Where the tool supports an interactive
   multi-select prompt, use it; otherwise ask the user to reply with the numbers
   (e.g. `1,3,4`), `all`, or `none`.
5. **Apply** the chosen findings using the `--update` apply logic (in-place edits),
   then report what changed. `none` → stop without writing. Review never rewrites
   silently — the user always chooses.

### Checklist

**Accuracy:**
- [ ] No local paths (`/Users/`, `/home/`, `C:\`)
- [ ] File paths / `file:line` references exist and are correct
- [ ] Class/function names are current; described behavior matches the code
- [ ] No signatures restated in prose (should reference code instead)
- [ ] Links to related docs work

**Quality:**
- [ ] No verbatim duplication across files
- [ ] Current-state and why are separated; gotchas documented
- [ ] Examples are concrete (not generic placeholders)

**Completeness:**
- [ ] No incomplete sections, placeholders, or TODOs
- [ ] Key interfaces covered (APIs, components, hooks, services, utilities)
- [ ] Missing `overview.md` (root or subdirectory) flagged
- [ ] Required sections present (Purpose, How it works, Gotchas)

### Output Format

```markdown
## Documentation Review: {scope}

### Critical (fix now)
1. {file}:{line} - {issue}

### High Priority (fix soon)
2. {file} - {issue}

### Suggestions
3. {file} - {improvement}
```

Number findings sequentially across all tiers so the user can select by number.

---

## Update Mode (`--update`)

Sync existing docs to the current code — the end-of-feature "make sure what changed
is reflected" pass. Edits in place; never appends a changelog.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Staged code changes | `git diff --cached --name-only`; if empty, fall back to unstaged (`git diff --name-only`) and open with a one-line note: "Nothing staged — syncing docs for unstaged changes instead." |
| `<target>` | A feature/area as a whole | All docs + code for that feature |
| `--all` | Whole project | Cross-check `docs/**` against source |

### Workflow

1. **Determine the changed scope** (above).
2. **Map** changed files/symbols → affected docs: grep `docs/**`, `README.md`,
   `CLAUDE.md` for the changed symbols/topics to find the docs describing them.
3. **Apply in place**: edit each affected doc to match the current code — **replace**
   the stale parts, preserve formatting/style, stay concise (current state, not
   history). Update the "how it works now" sections; leave "why" alone unless the
   decision itself changed.
4. **New behavior with no doc**: if there's a clear home pattern (e.g.
   `docs/features/<name>.md`), create that doc from the template; otherwise list it
   as an undocumented gap and suggest `--generate`. Don't create docs with no obvious
   home.
5. **Fan out**: if >5 affected files/docs, spawn one sub-agent per doc/area, merge.
6. **Report**: which docs were edited and what was synced; any gaps left for
   `--generate`.

---

## Generate Mode (`--generate`)

Create documentation for code that isn't documented yet, following the principles
and `references/generate-templates.md`.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| `<target>` | Specific file/module/feature | Read the code, generate docs |
| `--staged` | Staged code changes | Generate docs for what changed |
| `--unpushed` | Unpushed code changes | Generate docs for what changed across unpushed commits (`git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD`). If nothing is unpushed or detection is unreliable (no remote/upstream, root-commit walk-back), stop and ask. |

### Workflow

1. **Read the code** - understand what it does and how it works.
2. **Check for existing docs** - if they exist, prefer `--update` instead.
3. **Generate** following the templates (current-state + why; `file:line` refs, not
   restated signatures).
4. **Place appropriately** in `docs/`:
   - `docs/prd/` for product behavior / requirements — what each feature does for the
     user. This is the layer that mirrors `docs/product/` use cases (owned by
     `review-product`) and tracks the implementation. Document features here as they're
     built.
   - `docs/tech/` for technical implementation
   - `docs/features/` for feature documentation
   - `docs/api/` for API documentation
   - Ensure a root `docs/overview.md` index exists and a section `overview.md` in any
     new subdirectory.
5. **Install the per-repo update trigger.** After writing docs, append a concise
   docs note to the project-local `./CLAUDE.md` (or `AGENTS.md` if that's what the
   project uses) — **idempotent**, skip if already present:
   > ## Documentation
   > Project docs live in `docs/` (start at `docs/overview.md`). After completing a
   > feature, run `doc --update` to keep them current.
   This is the moment a project opts into maintaining docs, so the trigger is
   installed exactly here — not globally.

---

## Examples

**Not sure what the docs need — just triage them:**
> /doc

Surveys `docs/` (presence, overview index, tree) and the code surface, then
reports a numbered plan: which areas have no docs (Generate), which docs are
stale vs the code (Update), which have quality issues (Review), and what's
healthy. Asks which to run and executes your picks in place.

**Sync docs after finishing a feature:**
> /doc --update

Maps staged code changes to the docs that describe them and rewrites those sections
in place to match the new behavior, reporting what it touched. Run it while you still
have the build context.

**Review a feature's docs and pick fixes:**
> /doc --review payments

Reviews every doc covering payments against the current code, lists numbered findings
by priority, then asks which to apply — applying your selection in place.

**Generate docs for a new service module:**
> /doc --generate lib/services/notification_service.dart

Reads the service, generates a module doc in `docs/tech/` (Purpose, How it works, Key
entry points, Gotchas, Why), ensures the `docs/overview.md` index exists, and adds the
update-trigger note to the project's CLAUDE.md.

## Troubleshooting

### Assess proposes documenting the entire codebase on a fresh repo
**Cause:** Greenfield triage over-reaching. **Solution:** Assess should pick a
*starter set* — root `overview.md` plus the few highest-value modules — not one
doc per file. If it listed everything, narrow to the entry points and core
modules; the rest follows as those areas are built (via `--update`/`--generate`).

### Assess flags a doc as stale that's actually fine (or misses a stale one)
**Cause:** Staleness is a heuristic (doc edit time vs code change time, broken
refs) and can mis-fire. **Solution:** Assess only *proposes* — confirm before
running Update. For a definitive check, run `--review <target>`, which compares
the doc against the code directly.

### `--update` reports "nothing staged"
**Cause:** No staged changes. **Solution:** It falls back to unstaged changes
automatically (with a note). To target something specific, run `doc --update <feature>`
or `git add` the files first.

### `--update` found new behavior but didn't document it
**Cause:** No existing doc and no clear home directory for it. **Solution:** It's
listed as a gap — run `doc --generate <target>` to create the doc, which also wires
the home into the docs tree.

### Generated docs restate function signatures
**Cause:** The generator should reference code, not copy it. **Solution:** Re-run
`--update` on the doc; signatures belong as `file:line` references (principle 3), with
prose describing the contract and why.

### Review finds no issues but coverage is incomplete
**Solution:** Use `--all` to scan the full `docs/` tree against source modules; missing
docs for key modules surface as completeness gaps.

## Notes

- Default (no args) is assess mode: survey the docs state, propose an action
  plan, and run the user's picks. It's the entry point when you don't yet know
  what the docs need.
- All modes share the same principles and the compare-to-code engine.
- Reach for an explicit mode when you already know the action: `--update` at the
  end of feature work; `--review` for a periodic human-facing audit;
  `--generate` for greenfield docs; assess when unsure.
- Sub-agents parallelize large reviews/updates/generations (>5 files).
- Three-layer model: `docs/product/` (user/why — owned by `review-product`) →
  `docs/prd/` (product behavior — owned by `doc`, this layer) → implementation.
  `doc` keeps `docs/prd/` ↔ code in sync; `review-product` checks `docs/product/` ↔
  `docs/prd/`. `doc` never touches `docs/product/`.
