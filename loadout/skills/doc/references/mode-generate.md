# Generate Mode (`--generate`)

Create documentation for code that isn't documented yet, following
`references/principles.md` and `references/generate-templates.md`.

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| `<target>` | Specific file/module/feature | Read the code, generate docs |
| `--staged` | Staged code changes | Generate docs for what changed |
| `--unpushed` | Unpushed code changes | Generate docs for what changed across unpushed commits (`git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD`). If nothing is unpushed or detection is unreliable (no remote/upstream, root-commit walk-back), stop and ask. |

## Workflow

1. **Read the code** - understand what it does and how it works.
2. **Check for existing docs** - if they exist, prefer `--update` instead.
3. **Generate** following the templates (current-state + why; `file:line` refs, not
   restated signatures).
4. **Place appropriately**, per the repo's **Doc Profile** (see `references/principles.md`
   for the selection test; default to Lean when ambiguous). Where each kind of doc goes:
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

## Troubleshooting

### Generated docs restate function signatures
**Cause:** The generator should reference code, not copy it. **Solution:** Re-run
`--update` on the doc; signatures belong as `file:line` references (principle 3), with
prose describing the contract and why.
