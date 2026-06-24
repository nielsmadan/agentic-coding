---
name: doc
description: "Assess documentation state and run the right action (default, no args): survey what exists, find gaps / staleness / quality issues, then route into generate, update, or review. Explicit modes: review (--review), update (--update), generate (--generate <target>), harvest a session log (--session). Scope --staged, --all, or context. Use when unsure what the docs need, or for doc creation, freshness, and quality."
argument-hint: "[ (no args = assess) | --review | --update | --generate <target> | --session --md <file>] [--staged | --all]"
---

# Doc

Assess, review, update, and generate documentation following consistent principles.

## Which mode runs — read first

**Bare `/doc` with no mode flag → Assess, over the whole repo. Always.**

- Do **not** infer `--update` or `--review` from conversation context. "We just
  finished a feature", "just committed", or "recent changes" do **not** narrow a
  bare `/doc` — assess surveys the *entire* docs state. Bare `/doc` is **not**
  the end-of-feature sync.
- Run an explicit mode **only when the user types the flag** (`--update`,
  `--review`, `--generate`, `--session`). Don't pick one for them.
- Don't substitute "I know what's needed, so I'll just update/review." That
  shortcut is exactly the bug assess exists to prevent — run the full assess and
  let its plan (which includes Generate/structure) surface what you'd skip.
- If you catch yourself about to run update or review from a bare `/doc`, stop
  and run assess instead.

## Modes

All modes share one engine — *compare the docs against the current code
reality* — and differ only in what they do with the result:

| Mode | Intent | Writes? | Default scope |
|------|--------|---------|---------------|
| **(no args) — assess** | Survey docs state, propose & run an action plan | No → plan, then runs your picks | whole docs tree + key source |
| `--review [target]` | Assess accuracy / completeness / quality | No → findings, then interactive apply | context (or `<target>`) |
| `--update [target]` | Sync existing docs to current code | Yes — in place, replace stale parts | staged code, falling back to unstaged |
| `--generate <target>` | Create docs that don't exist yet | Yes — new files | the target |

**Assess is the default** — it's what a bare `/doc` runs (see "Which mode runs"
above). It surveys, classifies, and routes into the three modes below. The
explicit modes are opt-in via their flag: `--review` and `--update` are the same
comparison (review reports and lets you pick what to apply; update applies
directly from a diff); `--generate` is for greenfield.

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
- `docs/explain/` (the `explain` skill), `docs/product/` (the `review-product`
  skill), and frozen planning artifacts like `docs/superpowers/` (plans/specs)
  are owned elsewhere / not code-derived. `doc` leaves them alone: exclude them
  from `--all` and never sync them to code. Crucially, their presence does **not**
  count as a docs tree — a repo whose only `docs/` content is `docs/superpowers/`
  is greenfield for assess's purposes. `docs/prd/` *is* `doc`'s — the
  product-behavior layer it keeps in sync with the implementation.

## Assess Mode (default)

The no-args entry point. Use it when you don't know what the docs need: it
surveys the current state, classifies what's required, hands you a prioritized
action plan, then runs the parts you choose by delegating to the other modes.
It never writes without your go-ahead — the plan comes first.

### Workflow

1. **Survey the landscape.** Separate the **two doc layers** — they're assessed
   differently and conflating them is the classic mistake (a repo with a README
   looks "documented" when it has no real docs tree):
   - **Ad-hoc top-level docs** — `README.md`, `CLAUDE.md`, `AGENTS.md`. Nearly
     every repo has these; their existence does **not** mean the project has a
     docs tree.
   - **Structured `docs/` tree** — `docs/prd/` (product behavior), `docs/tech/`
     (implementation), `docs/features/`, `docs/api/`, with `overview.md`
     indexes. This is the layer `--update`/`--generate` maintain.
   - **Owned elsewhere / frozen — do NOT count as the structured layer:**
     `docs/explain/` (the `explain` skill), `docs/product/` (`review-product`),
     and frozen planning artifacts like `docs/superpowers/` (plans/specs). Their
     presence does **not** make a project "documented" — exclude them from the
     glob and never sync them to code.
   - Glob `docs/**/*.md` (minus the excluded dirs); note count and tree. Sketch
     the code surface worth documenting: top-level modules, features, services,
     APIs.
   - For a large tree (>~15 docs or a big codebase), fan out — one sub-agent per
     check in step 2 — and merge.

2. **Run all three checks and reach a verdict for EACH lane.** Never silently
   skip a lane: if a lane has nothing, say so *and why* (this is what stops
   assess from quietly collapsing into "just review the existing docs").
   - **Gaps → Generate.** *The lane most often missed.* First answer the
     structure question explicitly: **is there a structured `docs/` tree
     (`docs/prd` and/or `docs/tech`)?** If not — only top-level docs and/or
     frozen artifacts — decide *out loud* whether to propose creating one
     (`docs/prd/` for what each feature does, `docs/tech/` for how it's built),
     sized to the project:
       - Non-trivial app/library (multiple features or modules) → **recommend
         generating** the starter structure (root `docs/overview.md` + a
         `docs/prd` and/or `docs/tech` seed for the highest-value areas).
       - Tiny project where `README` + `CLAUDE.md` genuinely cover everything →
         record it as **considered and skipped, with the reason** — do not just
         omit it. The user decides if it's worth it.
     Then the ordinary gaps: source areas with no doc, missing `overview.md`.
     Don't over-reach to one-doc-per-file.
   - **Staleness → Update.** Docs whose code changed after the doc was last
     touched (`git log -1 --format=%cd -- <doc>` vs recent commits to the code
     it covers), and docs referencing files / `file:line` / symbols that no
     longer exist.
   - **Quality → Review.** A light principles pass: local paths, restated
     signatures, verbatim duplication, placeholders/TODOs, missing required
     sections.

3. **Report state + action plan.** Always emit *this* assess report (titled
   **Docs Assessment**) — not a plain "Documentation Review". Reviewing existing
   docs is only the Quality lane; it must never replace the Generate (structure/
   gaps) and Update (staleness) lanes. One categorized, sequentially-numbered
   list, with **every lane present even when empty**:
   ```markdown
   ## Docs Assessment: {repo/scope}
   State: {top-level docs: README/CLAUDE/AGENTS present?} · {structured docs tree: yes / NONE (only top-level + frozen artifacts)} · {N living docs · overview index present/missing}

   ### Generate (missing / structure)
   1. {e.g. "No docs/ tree — recommend docs/prd + docs/tech seed" OR "Considered a docs/ tree — skipped: small library, README+CLAUDE cover it"}

   ### Update (stale)
   2. {doc} — {code changed / broken ref}   (or: "none — docs match code")

   ### Review (quality)
   3. {doc} — {issue}   (or: "none — checked, conforms")

   ### Healthy
   - {what's already fine — so the user knows it was checked}
   ```
   Number actionable findings sequentially across tiers so the user can select by number.

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

### Assess only reviewed the existing docs and never considered creating a `docs/` tree
**Cause:** Top-level docs (README/CLAUDE/AGENTS) — or frozen `docs/superpowers/`
artifacts — made it conclude "docs exist, just check them," collapsing into a
plain review and skipping the **Generate** lane. **Solution:** Assess must reach
a verdict on *every* lane, including the structure question ("is there a
`docs/prd`/`docs/tech` tree? if not, recommend one or record why it's skipped").
A README is not a docs tree; frozen plan/spec artifacts don't count. If assess
output is titled "Documentation Review" rather than "Docs Assessment," it ran the
wrong mode — re-run bare `/doc`.

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
