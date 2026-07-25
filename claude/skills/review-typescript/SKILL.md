---
name: review-typescript
description: TypeScript-specific code review focused on JUDGMENT-level type design a linter can't decide — type modeling (make invalid states unrepresentable), inference-vs-annotation calls, and casts/`any` that hide a real modeling problem. Deliberately does NOT duplicate typescript-eslint. Auto-invoked by `code-review` on TypeScript projects. Triggers "review typescript", "typescript review", "type design review".
argument-hint: '[--staged | --unpushed | --changed | --all | --multi]'
effort: high
---

# Review TypeScript

TypeScript review that covers what a **type-aware linter cannot decide for you** — how types are *modeled*, when to *annotate vs infer*, and whether a cast or `any` is papering over a design problem. These are judgment calls; the mechanical rules are ESLint's job.

## Relationship to typescript-eslint (read first)

**This skill assumes `typescript-eslint` handles the mechanical layer.** Do NOT re-flag anything a lint rule catches — that's noise and it duplicates CI. Specifically, do **not** report:

- Redundant/unnecessary assertions (`no-unnecessary-type-assertion`), explicit `any` (`no-explicit-any`), unsafe `any` flow (`no-unsafe-*`), non-null `!` (`no-non-null-assertion`)
- `@ts-ignore`/`@ts-expect-error` without a reason (`ban-ts-comment`)
- Floating/misused promises, `await`-thenable, throw/reject non-Error (`no-floating-promises`, `no-misused-promises`, `only-throw-error`)
- Dangerous built-ins `Function`/`{}`/wrapper objects (`no-unsafe-function-type`, `no-empty-object-type`, `no-wrapper-object-types`)
- Truthiness/nullish traps, `??` vs `||`, template-expression coercion (`strict-boolean-expressions`, `prefer-nullish-coalescing`, `restrict-template-expressions`)
- `import type`, `prefer-as-const`, trivially-inferrable annotations (`consistent-type-imports`, `prefer-as-const`, `no-inferrable-types`)
- Always-true/false conditions, single-use generics, exhaustive switches (`no-unnecessary-condition`, `no-unnecessary-type-parameters`, `switch-exhaustiveness-check`)

**One-time tooling recommendation (not a per-diff finding):** if the project's ESLint config is missing or isn't on `typescript-eslint` `strict-type-checked`, say so **once** at the top of the review and recommend enabling it — plus tsconfig `strict` and `noUncheckedIndexedAccess`. That single recommendation solves the whole mechanical class (including the classic "unnecessary cast slipped through" via `no-unnecessary-type-assertion`) far better than a reviewer eyeballing diffs. Then move on to the judgment work below.

Run on `.ts` / `.tsx` / `.mts` / `.cts`. Complements `review-cleancode` (SOLID/DRY/smells) — don't repeat it.

## Usage

```
/review-typescript                  # Review context-related code
/review-typescript --staged         # Review staged changes
/review-typescript --unpushed       # Review files changed across all unpushed commits
/review-typescript --changed        # Review unstaged changes
/review-typescript --all            # Full codebase audit (parallel agents)
/review-typescript --multi          # Also get external advisor opinions
```

## Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related code | Files from the current conversation context. If no context, ask the user to specify files or use `--staged`/`--changed`/`--all`. |
| `--staged` | Staged changes | `git diff --cached --name-only` |
| `--unpushed` | Files changed across unpushed commits | `git diff --name-only $(git rev-list HEAD --not --remotes \| tail -1)^..HEAD` |
| `--changed` | Unstaged changes | `git diff --name-only` |
| `--all` | Full codebase | Glob `*.ts`/`*.tsx`/`*.mts`/`*.cts`, parallel agents |
| `--multi` | Add external opinions | Combines with any scope above; invokes `second-opinion --quick` |

`--unpushed` derives its range from `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If nothing is unpushed, or there is no remote/upstream (or the range walks back to the root commit) so it can't be determined reliably, stop and ask the user to pick another scope. Restrict the resolved file list to TypeScript extensions before reviewing.

## Workflow

1. **Determine scope** (see table) and filter to TypeScript files only.
2. **Read CLAUDE.md** in the repo root for project conventions.
3. **Check the lint baseline once.** Look for `eslint.config.*`/`.eslintrc*` and whether it extends `typescript-eslint` `strict-type-checked` (or `recommended-type-checked`). If absent, emit the one-time tooling recommendation above and note that mechanical findings are out of scope for this review.
4. **Review each file** against the three judgment categories below.
5. **Parallelize** if scope has >5 files: one sub-agent per category, merge and dedupe.
6. **External opinions** (if `--multi`): invoke `second-opinion --quick` with this prompt:

   ```
   Read-only TypeScript review. Assume typescript-eslint already handles mechanical rules — do NOT repeat lint-level findings. Focus on TYPE DESIGN judgment: are invalid states representable that shouldn't be? Are types modeled with unions of interfaces or a bag of optional fields? Are functions returning wider types than callers need? Is inference used where it could be, and are annotations added only where they serve a purpose (definition-site checking of complex literals, public-API contracts)? Do any casts/`any` compile but hide a wrong upstream type? 300 words or less.
   ```

   Wait for all external results before proceeding.
7. **Classify severity** and **report**, grouped by severity.

## Checklist (judgment only)

### 1. Type modeling & design

The core value. A linter checks that types are *consistent*; only a human checks that they're *right*.

- **Invalid states are representable.** Flag a type where contradictory or impossible combinations can be constructed — e.g. `{ isLoading: boolean; data?: T; error?: E }` allows loading-with-data-and-error simultaneously. Recommend a discriminated union so illegal states won't type-check. *(Effective TS Item 29 — "make invalid states unrepresentable.")*
- **Bag-of-optionals instead of a union of interfaces.** `interface Shape { kind; radius?; sideLength? }` should be `type Shape = Circle | Square`, each with only its own required fields. *(Effective TS Item 34.)*
- **Outputs wider than callers need.** A function whose return type includes `| null`, `| undefined`, or `| string` that no caller actually wants forces defensive handling everywhere. Be liberal in inputs, strict in outputs. *(Effective TS Item 30.)*
- **`null`/`undefined` scattered through the interior** instead of pushed to the perimeter. Flag types that bake nullability into shared aliases or sprinkle nullable fields deep in the model; normalize at the boundary so interior code deals in non-null values. *(Effective TS Items 32/33.)*
- **Optional overload.** Many `?` fields "just in case" multiply the states callers must handle. Flag types that are mostly-optional when the real object usually has everything. *(Effective TS Item 37.)*
- **In-band sentinels.** `-1`/`0`/`""` overloaded to mean "not found"/"none" instead of a distinct type or `null`. *(Effective TS Item 36.)*
- **Hand-copied shapes that will drift.** A type that manually restates a subset of another type's fields should derive from it via `Pick`/`Omit`/`Partial`/`Required`/`Record`/`ReturnType<typeof fn>` so it stays in sync when the source changes. Judgment call: derive when there's a real source-of-truth relationship; don't force utility-type gymnastics where an independent type is genuinely clearer. *(Effective TS Item 15.)*
- **Interchangeable primitives that shouldn't be.** Several `string` IDs (`userId`, `postId`) or unit-bearing `number`s that can be swapped at a call site with no error — consider a branded/nominal type *only if* mix-ups are a real risk here. Note the cost (ergonomics); don't recommend brands reflexively. *(Effective TS Item 64.)*

### 2. Inference vs. annotation

Default to inference; annotate only when it **serves a purpose**. The judgment is *which* is which — the trivial cases (`const n: number = 5`) are ESLint's `no-inferrable-types`, so don't report those.

- **Prefer inference where the initializer already yields the right type.** Flag annotations that merely restate an inferred type *and* cost you nothing to drop — but only when removing them changes nothing (don't flag an annotation that's narrowing or widening on purpose).
- **Do annotate hand-authored complex objects** (config objects, fixtures, lookup tables, large literals). An annotation there surfaces a mistake **at the definition site** immediately, instead of as a confusing error at some distant use site — this is a *good* annotation, flag its **absence** on nontrivial literals, not its presence.
- **Prefer `satisfies` over a colon annotation for literals when you want validation *and* narrow inferred types.** `const routes = {...} satisfies Record<string, Handler>` type-checks the literal while keeping the exact keys for autocomplete; `const routes: Record<string, Handler> = {...}` widens them away. Flag `: WideType = { literal }` where narrow keys/values are later needed. *(Total TypeScript / Pocock; Effective TS Item 9.)*
- **`as` is not an annotation.** Flag `const x = { ... } as SomeType` used to *label* a literal: `as` silences errors rather than checking, so a missing/renamed field passes silently and breaks at runtime. Recommend a colon annotation or `satisfies`. *(This is the judgment cousin of the linted redundant-cast rule — here the cast is being misused as documentation.)*
- **Return-type annotations on public API boundaries, not internals.** Recommend an explicit return type on exported/public functions (locks the contract, catches accidental widening). Do **not** flag missing return types on internal/local functions where inference is fine and annotations are noise. *(Conditional — weigh the function's visibility. Pocock: "don't use return types, unless…"; Effective TS Items 30/67.)*
- **Export types that appear in a public API's signatures.** Flag an exported function whose params/return reference an un-exported type — consumers can't name it. *(Effective TS Item 67.)*

### 3. Casts & escape hatches — the judgment residue

ESLint flags casts that are *provably redundant* and *provably unsafe*. What's left for a human:

- **A cast that compiles but hides a wrong upstream type.** `return rows as OrderDTO[]` where `rows` is `Record<string, unknown>[]`: the cast is load-bearing (lint won't call it unnecessary) but it exists only because the DB layer is mistyped. The fix is upstream — type the query result — not the cast. This is the highest-value cast finding and it's pure judgment.
- **A cast/`any` standing in for validation at a trust boundary.** `JSON.parse(s) as Config`, `res.data as User`, `event.target as HTMLInputElement` assert a shape that was never checked. For parsed/network/DOM data, recommend a runtime guard or schema (the assertion is a claim, not a proof). Judgment: legitimate at genuinely-safe boundaries, a bug waiting to happen for external data.
- **`any`/suppression that masks a modeling gap.** Where `any` (or a `@ts-expect-error` that lint permits because it has a comment) is hiding a type that *could* be modeled, say what the right type is. The point isn't "there's an `any`" (lint's job) — it's "here's the model that removes the need for it."

State your reasoning for each finding. "Cast hides that `getUser` is mistyped as `any`" is a finding; "there's a cast here" is not (and is probably already lint-flagged).

## Severity

- **Critical**: a type-modeling flaw that lets illegal state reach runtime and cause a crash/corruption (invalid-states-representable in a load-bearing model; a boundary cast on unvalidated external data that will throw on malformed input).
- **High**: a modeling problem that will cause bugs or force error-prone handling as the code evolves (outputs too wide, cast hiding a wrong upstream type, hand-copied type that will silently drift).
- **Medium**: annotation/inference misuse (`as`-as-label, missing definition-site annotation on a complex literal, missing public-API return type), sentinel values, over-optional types.
- **Suggestion**: nominal-type opportunities, DRY-via-utility-type refactors where the current code is merely repetitive, not buggy.

## Output Format

```markdown
## TypeScript Review: {scope}

### Lint baseline
{One line: does the project run typescript-eslint strict-type-checked? If not, the one-time recommendation. Omit if it does.}

### Critical (illegal state can reach runtime)
- {file}:{line} — {category}: {description}
  **Why it's not a lint finding:** {what judgment this needed}
  **Impact:** {what breaks}
  **Fix:** {model change / boundary validation — with code}

### High (modeling problems that will cause bugs)
- {file}:{line} — {category}: {description}
  **Fix:** {solution}

### Medium (annotation/inference & type-design)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {opportunities}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection.

## Examples

**Invalid state representable:**
> /review-typescript --staged

Finds a `FetchState` type `{ loading: boolean; data?: T; error?: string }` — nothing prevents `loading: true` with both `data` and `error` set. Reports High with a discriminated-union rewrite. Not a lint finding: the type is internally consistent; only a human knows the states are illegal.

**Cast hiding a mistyped source:**
> /review-typescript --changed

Finds `const total = order.items as LineItem[]` where `order.items` is typed `any` (from an untyped API client). Reports High — fix the client's return type; the cast is a symptom. `no-unnecessary-type-assertion` stays silent because the cast is load-bearing.

**Good annotation missing:**
> /review-typescript

A 40-line hand-written `const config = {...}` has no type, so a typo in a nested key only errors at a distant consumer. Reports Medium — add `satisfies AppConfig` for definition-site checking while keeping the narrow inferred shape.

## Troubleshooting

### Findings overlap with ESLint
**Solution:** They shouldn't. If a finding maps to a named typescript-eslint rule, drop it and (if the project doesn't run that rule) fold it into the one-time lint-baseline recommendation instead. This skill only reports what a type-aware linter can't judge.

### Can't tell if a boundary cast is safe
**Solution:** Trace where the value comes from. In-process, already-typed data → the cast may be fine (or redundant, i.e. lint's problem). External/parsed/DOM data → recommend a runtime guard; the type system can't vouch for data it never saw.

## Notes

- Model first, annotate second, cast last. Most cast findings dissolve once the underlying type is modeled correctly.
- Respect project conventions in CLAUDE.md (a codebase may deliberately allow `null`, prefer `interface`/`type`, etc.).
- Don't be dogmatic: brands, utility-type derivation, and satisfies all have ergonomic costs — recommend them where they prevent real bugs, not everywhere they're possible.
- Sources: *Effective TypeScript*, 2nd ed. (Vanderkam, 2024); Total TypeScript (Pocock); the TypeScript Handbook. typescript-eslint owns the mechanical rules referenced above.
