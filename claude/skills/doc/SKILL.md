---
name: doc
description: "Documentation review (--review, default), update (--update), or generation (--generate). Scope --staged, --all, or context. For doc quality, freshness, and creation."
argument-hint: "[--review | --update | --generate <target>] [--staged | --all]"
---

# Doc

Review, update, and generate documentation following consistent principles.

## Modes

All three modes share one engine — *compare the docs against the current code
reality* — and differ only in what they do with the result:

| Mode | Intent | Writes? | Default scope |
|------|--------|---------|---------------|
| `--review` (default) | Assess accuracy / completeness / quality | No → findings, then interactive apply | context (or `<target>`) |
| `--update [target]` | Sync existing docs to current code | Yes — in place, replace stale parts | staged code, falling back to unstaged |
| `--generate <target>` | Create docs that don't exist yet | Yes — new files | the target |

`--review` and `--update` are the same comparison; review reports and lets you pick
what to apply, update applies directly from a diff. `--generate` is for greenfield.

## Usage

```
/doc                              # Review docs related to current context (default)
/doc --review payments            # Review docs for a feature, then pick fixes to apply
/doc --review --all               # Review all docs (parallel agents)
/doc --update                     # Sync docs for staged code changes (end of a feature)
/doc --update auth flow           # Sync all docs for a feature/area
/doc --generate <target>          # Generate docs for file/module/feature
/doc --generate --staged          # Generate docs for staged code changes
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

## Review Mode (`--review`)

Default mode. Assesses docs against the principles, then offers to apply fixes.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Find docs related to recent conversation |
| `<target>` | A feature/area as a whole | Find all docs covering that feature |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` (excluding `docs/explain/`, `docs/product/`) + `README.md` + `CLAUDE.md` |

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

- Default is review mode with context-based scope.
- All modes share the same principles and the compare-to-code engine.
- Use `--update` at the end of feature work; `--review` for periodic human-facing
  audits; `--generate` only for greenfield docs.
- Sub-agents parallelize large reviews/updates/generations (>5 files).
- Three-layer model: `docs/product/` (user/why — owned by `review-product`) →
  `docs/prd/` (product behavior — owned by `doc`, this layer) → implementation.
  `doc` keeps `docs/prd/` ↔ code in sync; `review-product` checks `docs/product/` ↔
  `docs/prd/`. `doc` never touches `docs/product/`.
