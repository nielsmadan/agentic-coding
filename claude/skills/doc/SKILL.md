---
name: doc
description: "Assess documentation and run the right action (default, no args): a context-aware assess that, with uncommitted changes, checks those changes are documented, and on a clean tree does a whole-repo review — finding gaps / staleness / quality issues and routing into generate, update, or review. Explicit overrides: review (--review), update (--update), generate (--generate <target>), harvest a session log (--session); scope with --all, --staged, --unpushed, or a target. Use when unsure what the docs need, or for doc creation, freshness, and quality."
argument-hint: "[ (no args = context-aware assess) | --review | --update | --generate <target> | --session --md <file>] [--all | --staged | --unpushed]"
effort: high
---

# Doc

Assess, review, update, and generate documentation following consistent principles.

## Which mode runs (read first)

**Bare `/doc` = context-aware assess.** It adapts its *scope* to git state but always runs
all three lanes (Generate / Update / Review) and never writes without a plan, it proposes,
then runs your picks.

- **Dirty tree (staged or unstaged changes) → "is what I just did documented?"** Center the
  assess on the changed files: are the docs covering them still accurate (**Update** lane),
  and does new behavior need a doc (**Generate** lane)? Add a quick whole-repo glance for
  structural gaps and obvious staleness so it doesn't tunnel-vision. Lead with the
  changed-files verdict. Staged wins; fall back to unstaged.
- **Clean tree → general review.** Whole-repo assess across all three lanes.

**The guard that still holds** (this is why the skill used to force whole-repo): auto-scoping
to the diff is fine, but **never collapse into a single silent action and never skip the
Generate/structure question.** Dropping a lane, or writing without showing a plan, is the bug,
not the narrowing. If the changed files reveal a missing docs tree or a bloated instruction
file, that surfaces even on a one-file diff.

**Explicit flags override** the auto-scope and auto-mode:
- Scope: `--all` (force whole repo), `--staged` / `--unpushed`, or `<target>`.
- Mode: `--update` / `--review` / `--generate <target>` / `--session` force that action
  regardless of git state.

## Modes

All modes share one engine — *compare the docs against the current code
reality* — and differ only in what they do with the result:

| Mode | Intent | Writes? | Default scope |
|------|--------|---------|---------------|
| **(no args) — assess** | Survey docs state, propose & run an action plan | No → plan, then runs your picks | **auto: changed files if the tree is dirty, else whole repo** |
| `--review [target]` | Assess accuracy / completeness / quality | No → findings, then interactive apply | context (or `<target>`) |
| `--update [target]` | Sync existing docs to current code | Yes — in place, replace stale parts | staged code, falling back to unstaged |
| `--generate <target>` | Create docs that don't exist yet | Yes — new files | the target |
| `--session --md <file>` | Harvest durable knowledge from a session log into the docs | Yes — after preview | the conversation md (see Session Mode) |

**Assess is the default** — it's what a bare `/doc` runs (see "Which mode runs"
above). It surveys, classifies, and routes into the three modes below. The
explicit modes are opt-in via their flag: `--review` and `--update` are the same
comparison (review reports and lets you pick what to apply; update applies
directly from a diff); `--generate` is for greenfield.

## Usage

```
/doc                              # Context-aware assess: dirty tree -> check the changes are documented; clean tree -> whole-repo review
/doc --all                        # Force a whole-repo assess even when there are uncommitted changes
/doc --staged                     # Assess, scoped to what staged changes touch (explicit)
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

### 5. Index for orientation, not completeness
- Add a root `docs/overview.md` **only once there are ~3+ living docs** to point to.
  Below that, the entry-point map in `AGENTS.md` is the index; a second index file is
  pure overhead.
- Add a subdirectory `overview.md` **only** when that subdir holds enough docs that an
  agent would otherwise struggle to find the right one. Do **not** mandate one per
  directory.
- An index maps **intent and entry points, not every module.** Exhaustive "catalog the
  codebase" maps are largely ignored for navigation and actively mislead once stale, so
  keep them short and pointer-first.
- Answers: "Which doc do I need?" not "here is a list of everything that exists."

### 6. Document Gotchas
- Non-obvious behavior, common mistakes, platform quirks, things that seem like they
  should work but don't.

### 7. Concrete Examples & Agent-Optimized Writing
- Reference real implementations: `lib/services/foo.dart:123`.
- Clear, factual, active voice; short sentences; bullets over paragraphs.
- For files longer than ~100 lines, add a table of contents at the top.

### 8. Keep the always-loaded instruction file lean
The `AGENTS.md`/`CLAUDE.md` layer loads into **every** session, so every line is a
permanent token cost. This is the highest-leverage file and a different discipline
from the on-demand `docs/` tree; treat it as its own concern, not an afterthought.
- **Per-line test:** *"Would removing this line cause the agent to make a mistake?"* If
  not, cut it. A bloated instruction file makes the agent ignore the rules that matter.
- **Include only** what is (a) always/broadly relevant AND (b) non-derivable from code:
  build/test/lint commands, conventions that differ from tool defaults, gotchas, a
  one-line entry-point map, and pointers into `docs/`. **Exclude** anything greppable
  (directory layouts, framework names, signatures) and anything enforceable (make it a
  linter/hook, not prose).
- **Target roughly <200 lines.** Prefer positive phrasing over "don't" lists.
- Prefer `AGENTS.md` as canonical with `CLAUDE.md` a `@AGENTS.md` bridge (see the Bridge
  note under Doc Profiles).

---

## Doc Profiles (size the docs to the repo)

Pick the **smallest profile that holds the repo's non-derivable knowledge.** Assess
proposes a profile and the user confirms; when torn between two, propose the smaller and
say why.

### Choosing a profile: complexity, not line count
The trigger is **how many distinct, non-derivable knowledge areas** the repo has, not its
size. Count the subsystems with a protocol / mechanism / quirk you can't read off a single
file, plus the features with non-obvious behavior. Then:
- **~1-4 areas total** (or everything fits in `AGENTS.md` commands/conventions/gotchas):
  **Lean** (or **Minimal**). Flat `docs/<name>.md` + `decisions/` + `log/`; folders would be
  ceremony at this scale.
- **~5+ areas in *each* of "what it does" and "how it's built," evolving on different
  cadences**: **Structured**. Justify the two folders *independently* - keep `features/` only
  when there's real user-facing behavior worth specifying apart from code; keep `tech/` only
  when several subsystems carry non-derivable mechanisms. A library may warrant `tech/` and no
  `features/`; a behavior-rich but simple app the reverse.
- **loc is a weak tiebreaker, not the test.** A 20k-loc app bridging 3 terminals x 3 agents
  with protocol quirks earns Structured; a 200k-loc CRUD app with one model may only need
  Lean. Judge the knowledge, not the line count. When genuinely ambiguous, default to Lean.

### Two audiences (and where user docs go)
**Most repos do NOT need `docs/user/`** — it is not a default. It is warranted only when the
project has a distinct **end-user audience** (people who *use* it, not just build it) AND using
it is non-trivial enough that the README alone isn't enough.
- **Typical yes:** an open-source or distributed CLI / tool / app / framework that other people
  install and learn to use.
- **Typical no:** an internal service (its consumers are other systems, not readers), a library
  whose "usage" is just API reference (that belongs in `features/` / `tech/`), or a personal /
  solo project. Default to **no `user/` tree**; the README covers usage.
- Open-source is the common trigger, but the test is the **audience**, not the license: an
  internal tool handed to other teams can qualify; a solo open-source lib may not.
- **Orthogonal to the profile:** a Lean repo with users can have `docs/user/`; a Structured
  internal service may have none. Decide it separately from Minimal/Lean/Structured.

When such an end-user audience *does* exist, they're distinct from **builders** (contributors +
coding agents who *work on* it), and the two need different docs in different *formats* — one
doc can't serve both:
- **User docs** (`docs/user/`, plus the README): how to *use* it. Verbose, task-oriented,
  example-driven. Human-format. README links here; agents don't auto-load it.
- **Builder docs** (`docs/features/` + `docs/tech/`, entered via `AGENTS.md`): `features/` =
  *what* it does (terse behavior reference), `tech/` = *how* it's built. Concise, pointer-first.

The trees are not mirror images: `tech/` has many internals with no user counterpart; `user/`
has verbose walkthroughs with no terse counterpart. They may share a *subject* (e.g. "monorepos")
at different altitudes — that's fine (same topic, different depth), just never verbatim-duplicate.
Keep `user/` and `features/` from becoming duplicates by making them different *kinds* of doc:
**`features/` is terse and complete** (every feature, compact, `file:line`); **`user/` is verbose
and selective** (only tasks that need a walkthrough). Rule: README → `user/`, `AGENTS.md` →
`features/` + `tech/`; the two never cross-link.

The redundancy trap: for a tool whose users are developers and whose behavior is fully in the
README, a separate `features/` can just restate the README or the code. Keep `features/` only if
that terse index tells an agent something faster than reading the code or the user docs would.

`docs/user/` is a real, maintained tree (kept accurate as behavior changes, in human format),
**not** frozen scratch. Only a *published* docs site (outside `docs/`, e.g. `site/`) is out of scope.

### Minimal: tiny or single-purpose repo
```
AGENTS.md        # lean (Principle 8): commands, conventions, gotchas, one-line entry-point map
CLAUDE.md        # one line: @AGENTS.md   (+ Claude-only overrides if any)
```
No `docs/` tree. The README serves humans; `AGENTS.md` serves agents.

### Lean: DEFAULT for most repos (a handful of non-derivable areas)
```
AGENTS.md              # canonical, lean (Principle 8)
CLAUDE.md              # @AGENTS.md bridge
docs/
  decisions/           # ADRs: one file per decision, Context / Decision / Consequences,
    0001-<slug>.md     #   superseded-not-edited (append-only record — see Doc lifecycles)
  log/                 # OPTIONAL: incident post-mortems (Problem/Root-cause/Fix), dated,
    2026-...-<slug>.md #   append-only. Keep for recurrence-prone bugs; also lift the
                       #   reusable lesson into the relevant live doc / AGENTS.md gotcha
  <flow>.md            # one explanation doc per genuinely cross-cutting flow (auth, sync,
                       #   data pipeline) that no single source file reveals
  overview.md          # ONLY once there are ~3+ docs to index
```
No `docs/features`+`docs/tech` split. No per-directory `overview.md`. Each doc is
orientation plus non-derivable content, pointer-first (`file:line`, never pasted code).

### Structured: many distinct subsystems and features
Adds two doc-owned buckets on top of Lean, split by **altitude** (what vs how):
```
docs/
  product/     # who & why: personas, jobs        (owned by review-product, not doc)
  features/    # WHAT each feature does — current behavior   (doc)
  tech/        # HOW it's built: architecture, mechanisms, API internals   (doc)
  decisions/   # ADRs                             (doc)
  user/        # how to USE it — verbose human how-tos, README-linked (only if there are end users)
  overview.md  # index
```
- `features/` is the renamed `docs/prd/`, and it absorbs the behavior that older trees split
  across separate `docs/features/` and `docs/api/` dirs — one bucket for "what it does," not
  three near-synonyms.
- `tech/` carries only **non-derivable** how (architecture, cross-cutting flow, why-this-
  structure); it never restates code (Principle 3).
- The what/how split is a lifecycle separation (behavior changes on features, tech changes
  on refactors) and maps to how agents retrieve; it earns its keep only at this size.

Reserve Structured for repos big enough that the split earns its maintenance cost. Do
**not** reach for it just because an app "has multiple modules" — nearly every app does.
This is where `--update`/`--generate` do the most work.

### Right-sizing an existing tree (assess is not just for greenfield)
A profile that's **heavier than the repo warrants is a finding, not a fixed fact.** When a
repo carries a Structured tree it doesn't earn (small/simple for its size) **or** that tree
is drifting (stale catalogs, broken refs), **propose consolidating down** to the right
profile. Over-structured docs *cause* drift (more surface to keep in sync), so an
over-structured-and-stale tree is the worst case and the strongest reason to shrink it.
- "It already exists and is maintained" is a **sunk-cost argument, not a reason to keep
  overhead.** Judge the tree on whether the split is *actually earning its keep* (repo big
  enough AND docs fresh/used), not on its mere existence.
- Consolidation = **migrate and preserve, not delete.** Fold the genuinely non-derivable
  content (rationale, cross-cutting flows, gotchas) down into a few `docs/<flow>.md` +
  `decisions/`, and **drop the drift-prone exhaustive catalogs** (per-file/module tables
  the agent can grep anyway — Principle 3/5). Those tables were the staleness.
- It's a proposal under the Generate/structure lane; the user confirms before anything is
  moved or removed.

### Doc lifecycles (which docs `--update` syncs to code)
- **Live / current-state** — `features/`, `tech/`, `<flow>.md`, `overview.md`. `--update`
  keeps these in sync with the code. The bulk of the tree.
- **Append-only records** — `decisions/` (ADRs) and `log/` (incident post-mortems).
  Doc-owned and part of the tree, but **never rewritten to match code** (they intentionally
  describe past decisions/code). `--update` adds new entries and fixes broken links only; it
  does not sync their body. Extract any still-relevant lesson into a *live* doc so agents
  actually see it during related work.
- **Owned elsewhere / frozen** — `product/`, `explain/`, `user/`, `superpowers/`. `doc`
  doesn't sync these (see Gotchas). `docs/superpowers/` is gitignored scratch: when assess
  meets it, offer to **harvest any embedded decisions into `decisions/` ADRs, then (on
  confirmation) delete the completed/stale plans** to de-clutter — but never delete a plan
  that may still be driving in-progress work.

**Bridge note (all profiles):** prefer `AGENTS.md` as the canonical instruction file and
`CLAUDE.md` = `@AGENTS.md` (repo-portable, honored by both toolchains). When Generate
installs the update trigger, write it into `AGENTS.md` and ensure the `CLAUDE.md` bridge
exists, rather than editing `CLAUDE.md` directly.

---

## Gotchas
- `--update`/`--generate --staged` document uncommitted code that may change in
  review. If the code is revised but the docs are committed alongside, they drift.
- `--all` scope includes CLAUDE.md — the skill may propose edits to the project
  instructions file that governs its own behavior.
- **Not code-derived, not synced, and they don't count as a docs tree:** `docs/explain/`
  (the `explain` skill), `docs/product/` (`review-product`), and frozen `docs/superpowers/`
  (plans/specs). A repo whose only `docs/` content is `docs/superpowers/` is greenfield for
  assess. `docs/superpowers/` is gitignored scratch, harvest its decisions into ADRs then
  delete completed plans (see Doc lifecycles). By contrast `docs/features/` *is* `doc`'s.
- `docs/user/` is **NOT** frozen: it's the user-facing tree (see "Two audiences"). `doc`
  keeps it accurate in human how-to format; agents don't auto-load it. Only a *published*
  docs site (outside `docs/`) is out of scope.
- `docs/decisions/` and `docs/log/` are **append-only** (see Doc lifecycles): `--update`
  never rewrites their bodies, only adds entries / fixes links.

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
   - **Structured `docs/` tree** — `docs/features/` (what it does), `docs/tech/`
     (how it's built), `docs/decisions/` (ADRs), with `overview.md` indexes. This
     is the layer `--update`/`--generate` maintain. (`docs/features/` was formerly
     `docs/prd/`; it absorbs any legacy `docs/prd`, `docs/api` behavior.)
   - **User-facing tree — `docs/user/`:** verbose human how-tos, README-linked, its
     own audience/format (see "Two audiences" under Doc Profiles). Part of the project's
     docs, kept accurate when behavior changes, but not the terse agent-facing structured
     layer and not agent-loaded by default.
   - **Owned elsewhere / frozen — do NOT count as the structured layer:**
     `docs/explain/` (the `explain` skill), `docs/product/` (`review-product`),
     and frozen planning artifacts like `docs/superpowers/` (plans/specs). Their presence
     does **not** make a project "documented" — exclude them from the glob and never sync
     them to code.
   - Glob `docs/**/*.md` (minus the excluded dirs); note count and tree. Sketch
     the code surface worth documenting: top-level modules, features, services,
     APIs.
   - For a large tree (>~15 docs or a big codebase), fan out — one sub-agent per
     check in step 2 — and merge.

2. **Run all three checks and reach a verdict for EACH lane.** Never silently
   skip a lane: if a lane has nothing, say so *and why* (this is what stops
   assess from quietly collapsing into "just review the existing docs").
   - **Gaps → Generate.** *The lane most often missed.* First answer the
     structure question, then pick the **doc profile** that fits the repo
     (default to the smallest that covers it; see "Doc Profiles" above):
     Full profile definitions are under "Doc Profiles"; here just pick and act:
       - **Minimal** → lean `AGENTS.md` only; record it as **considered and skipped, with
         the reason**, don't just omit it.
       - **Lean** (the default) → `AGENTS.md` + bridge, `docs/decisions/`, a *handful* of
         `docs/<flow>.md`.
       - **Structured** → adds `docs/features/` + `docs/tech/`, only when the complexity test
         is met (per "Choosing a profile", not loc). Don't reach for it just because the app
         "has multiple modules" — nearly every app does.
     If the repo **already has a tree heavier than its profile warrants** (Structured on a
     small/simple repo, especially if it's drifting), that is itself a Generate/structure
     finding: **propose consolidating down** (migrate the non-derivable content into a few
     `docs/<flow>.md` + `decisions/`, drop the drift-prone catalogs). Don't rubber-stamp an
     over-sized tree just because it exists — see "Right-sizing an existing tree." When you
     meet gitignored `docs/superpowers/`, offer to harvest embedded decisions into
     `decisions/` and then delete the completed plans (on confirmation).
     Also check the **instruction file itself** (Principle 8): is `AGENTS.md`/`CLAUDE.md`
     bloated with derivable/enforceable content or over ~200 lines? That is a Generate/
     Review gap in its own right. Then the ordinary gaps: source areas with no doc,
     genuinely missing indexes. Don't over-reach to one-doc-per-file; when unsure between
     two profiles, propose the smaller and say why.
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
   State: {top-level docs: README/CLAUDE/AGENTS present?} · {instruction file: AGENTS.md/CLAUDE.md — ~N lines, lean / bloated} · {current profile: Minimal / Lean / Structured / none} · {N living docs · overview index present/missing}

   ### Generate (missing / structure)
   1. {e.g. "Small app, no docs/ tree — recommend Lean profile: AGENTS.md + docs/decisions + 1-2 flow docs" OR "AGENTS.md is 340 lines with restated dir layout — trim to lean" OR "Considered a docs/ tree — skipped: single-purpose repo, Minimal profile covers it"}

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

**Auto-scopes to git state** (see "Which mode runs"): a dirty tree centers the assess on the
changed files (plus a whole-repo glance); a clean tree assesses the whole docs tree + key
source. Override with `--all` (force whole repo), `--staged` / `--unpushed`, or a `<target>`
(one feature/area).

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

The `--review` action (assess is the default; this is the explicit override). Assesses docs
against the principles, then offers to apply fixes.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Find docs related to recent conversation |
| `<target>` | A feature/area as a whole | Find all docs covering that feature |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--unpushed` | .md files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` (excluding `docs/explain/`, `docs/product/`, `docs/superpowers/`) + `README.md` + `CLAUDE.md`. Include `docs/user/` (check for accuracy vs behavior, but it's human-format — don't flag verbosity). Include `docs/decisions/` + `docs/log/` for link/quality checks but never sync their bodies to code (append-only). |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope.

### Workflow

1. **Get file list** based on scope.
2. **Review** (directly if ≤5 files, parallel sub-agents if more), checking each doc
   against the current code — prioritize accuracy/completeness/staleness over prose.
3. **Report findings** by priority (see Output Format). For `docs/features/` docs, report
   divergences between the documented behavior and the implementation in **both directions**
   (doc describes behavior the code lacks; code has behavior the doc omits) without assuming
   either side is correct — the user reconciles. This is the implementation side of the
   three-layer check; `review-product` checks `docs/product/` ↔ `docs/features/`.
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
- [ ] Root `overview.md` present *if* ~3+ docs warrant an index (Principle 5); do not
      flag a missing per-directory `overview.md` unless that subdir clearly needs one
- [ ] Instruction file (`AGENTS.md`/`CLAUDE.md`) is lean: no derivable/enforceable
      content, roughly <200 lines (Principle 8)
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
   decision itself changed. **Skip append-only records** (`docs/decisions/`,
   `docs/log/`): never rewrite their bodies to match code — they describe the past on
   purpose. At most add a new entry or fix a broken link (see Doc lifecycles).
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
4. **Place appropriately**, per the repo's **Doc Profile** (see "Doc Profiles" for the
   selection test; default to Lean when ambiguous). Where each kind of doc goes:
   - `docs/<flow>.md` — cross-cutting flows (Lean, the common case).
   - `docs/features/` — **what** each feature does (Structured; mirrors `docs/product/`
     use cases, tracks the implementation).
   - `docs/tech/` — **how** it's built (Structured; non-derivable only, never restate code).
   - `docs/decisions/` — ADRs (why-this-way).
   - Root `docs/overview.md` index once ~3+ docs exist; a subdirectory `overview.md` only
     where a subdir warrants one (Principle 5), not by default.
5. **Install the per-repo update trigger.** After writing docs, add the trigger to the
   canonical instruction file (`AGENTS.md`, via the Bridge note pattern) — **idempotent**,
   skip if already present:
   > ## Documentation
   > Project docs live in `docs/` (start at `docs/overview.md`, or the file map in this
   > file for a Lean repo). After completing a feature, run `doc --update` to keep them
   > current.
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
a verdict on *every* lane, including the structure question ("what doc profile fits:
Minimal / Lean / Structured? if none exists, recommend one or record why it's skipped").
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

- All modes share the same principles and the compare-to-code engine.
- Bare `/doc` (context-aware assess) is the entry point when you don't know what the docs
  need. Reach for an explicit override when you already know the action: `--update` to force a
  sync, `--review` for a periodic human-facing audit, `--generate <target>` for one specific
  doc. Greenfield needs no flag, assess proposes the starter set on its own.
- Sub-agents parallelize large reviews/updates/generations (>5 files).
- Doctrine and structure live in one canonical place each: routing in "Which mode runs",
  profiles/audiences in "Doc Profiles", frozen-vs-append-only in "Doc lifecycles".
