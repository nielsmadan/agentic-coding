# Documentation Principles & Doc Profiles

Load this when you are about to *write, size, or judge* docs — assess (picking a
profile), review (conformance), update and generate (applying it). Routing alone
does not need this file.

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
- **Push depth behind a pointer.** A long procedure, checklist, or rule set belongs in a
  skill or a `docs/` file that gets loaded when relevant — not inline in the file that
  loads every session.
- Prefer `AGENTS.md` as canonical with `CLAUDE.md` a `@AGENTS.md` bridge (see the Bridge
  note below).

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
  doesn't sync these (see the Gotchas in SKILL.md). `docs/superpowers/` is gitignored scratch:
  when assess meets it, offer to **harvest any embedded decisions into `decisions/` ADRs, then
  (on confirmation) delete the completed/stale plans** to de-clutter — but never delete a plan
  that may still be driving in-progress work.

**Bridge note (all profiles):** prefer `AGENTS.md` as the canonical instruction file and
`CLAUDE.md` = `@AGENTS.md` (repo-portable, honored by both toolchains). When Generate
installs the update trigger, write it into `AGENTS.md` and ensure the `CLAUDE.md` bridge
exists, rather than editing `CLAUDE.md` directly.
