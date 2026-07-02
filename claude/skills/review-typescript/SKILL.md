---
name: review-typescript
description: TypeScript-specific code review — unnecessary type assertions/casts, `any`, non-null `!`, `@ts-ignore`, unsafe narrowing, and other TS-only smells that language-agnostic reviews miss. Auto-invoked by `code-review` on TypeScript projects. Triggers "review typescript", "check type casts", "typescript review".
argument-hint: [--staged | --unpushed | --changed | --all | --multi]
---

# Review TypeScript

TypeScript-specific review covering type-system misuse that a language-agnostic review misses. The headline concern is **unnecessary type assertions** — casts (`as`) and non-null assertions (`!`) that turn out not to be needed and slip through review, because a reviewer eyeballing the diff can't tell a load-bearing cast from a redundant one without checking the actual inferred types.

This skill is language-specific and complements `review-cleancode` (SOLID/DRY/smells) and the bug/logic pass — it does not repeat them. Run it on `.ts` / `.tsx` / `.mts` / `.cts` code.

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

## Verifying necessity (the whole point)

The core value of this skill over a naked read is that it **checks whether a cast is actually load-bearing** instead of assuming it is. For each assertion you flag, decide necessity with evidence, not vibes:

1. **Read the source type.** Trace what type the expression already has. If it's already assignable to the asserted type, the cast is pure noise — remove it.
2. **Prefer proving it with the compiler.** When a typechecker is available, the strongest evidence is: delete the assertion, run `npx tsc --noEmit` (or the project's typecheck script — check `package.json`), and see if an error appears. No error → the cast was unnecessary. Do this on a scratch copy or mention it as the suggested fix; don't leave edits behind unless asked.
3. **Distinguish "unneeded" from "papering over a real type error."** A cast that *is* needed to compile is often a symptom of a wrong upstream type (a mistyped return, a too-loose parameter, a missing generic). The right fix is usually to correct the source type, not to keep the cast. Flag these as "cast hides a type-modeling problem," separate from "cast is redundant."

State which of these you did for each finding. "Likely unnecessary — the expression is already `Foo`" is a real finding; "there's a cast here" is not.

## Workflow

1. **Determine scope** (see Scope table) and filter to TypeScript files only.
2. **Read CLAUDE.md** in the repo root for project-specific conventions (e.g. a project may permit `any` in test fixtures, or ban `@ts-ignore` outright). Respect them.
3. **Locate assertions and escape hatches fast.** Grep the scoped files for the high-signal patterns before reading closely:
   - `\bas\b` (assertions; ignore `import ... as` / `export ... as` re-exports)
   - `as any`, `as unknown as`
   - `!` non-null assertions (`\w!\.`, `\w!\)`, `\w!;`, `\w!,`)
   - `@ts-ignore`, `@ts-expect-error`
   - `: any`, `<any>`, `Array<any>`, `Record<string, any>`
   - `@ts-nocheck`
4. **Review each hit** against the checklist below, applying the necessity test.
5. **Parallelize** if scope has >5 files: spawn one sub-agent per checklist category, merge and dedupe.
6. **External opinions** (if `--multi`): invoke `second-opinion --quick`, which queries every advisor it has configured, with this prompt:

   ```
   Read-only TypeScript review. Review the TypeScript code in this repository (use `git diff --cached` for --staged, `git diff` for --changed, or read the relevant files). Focus on TYPE-SYSTEM misuse: unnecessary type assertions (`as`) and non-null assertions (`!`) that aren't needed to compile, `any`/`as any`/`as unknown as`, `@ts-ignore`/`@ts-expect-error` without justification, and casts that hide a real type-modeling problem. For each cast, judge whether it is actually load-bearing. Provide a focused review in 300 words or less.
   ```

   Wait for all external results before proceeding.
7. **Classify severity** (see below) and **report** grouped by severity.

## Checklist

### 1. Unnecessary type assertions (primary)

- **Redundant `as`**: expression is already assignable to the asserted type. `const x = foo() as User` where `foo(): User`. → remove.
- **Cast instead of narrowing**: `(x as Cat).meow()` after a check that could be a type guard (`if (isCat(x))`) or discriminated-union switch. The assertion silences the compiler without proving anything at runtime.
- **Cast hiding a type-modeling problem**: the cast *is* needed to compile, but only because an upstream type is wrong (bad return type, too-loose param, missing generic arg). Fix the source type; don't keep the cast.
- **`as` on DOM / JSON / external boundaries**: `document.getElementById('x') as HTMLInputElement`, `JSON.parse(s) as Config`, `event.target as HTMLInputElement`. These assert without validating — a legitimate cast point, but flag when runtime validation (a schema, a guard) is the safer intent, especially for parsed/network data.
- **Const assertion misuse**: `as const` is usually good; flag only where it's applied then immediately widened away.

### 2. `any` and unsafe escape hatches

- **Explicit `any`**: params, returns, fields, variables typed `any`. Prefer `unknown` + narrowing, a real type, or a generic. `any` disables *all* checking downstream, not just at the site.
- **`as any` / `as unknown as T`**: double-casts that launder an incompatible type. Almost always a real type mismatch worth fixing at the source.
- **Implicit any**: untyped params in non-inferable positions, untyped catch bindings used as typed. (Note if `noImplicitAny` is off — that's a config finding.)
- **Loose object types**: `Function`, `Object`, `{}`, `object` where a specific shape is known.

### 3. Non-null assertions (`!`)

- **Unnecessary `!`**: the value is already non-nullable per its type. → remove.
- **`!` masking a real nullable**: prefer optional chaining (`?.`), a guard/early return, or a default (`??`). A `!` that's wrong throws at runtime with no type-level warning.
- **`!` in class field declarations** (`foo!: T` definite-assignment): fine for DI/lifecycle, suspicious when the field is plainly assigned in the constructor (then it's just noise) or never assigned (then it's a latent bug).

### 4. Suppression comments

- **`@ts-ignore` without a reason** or where `@ts-expect-error` (which fails when the error goes away) is the safer choice.
- **`@ts-expect-error` that no longer suppresses anything** — stale, should be removed.
- **`@ts-nocheck`** at file scope — almost always unacceptable in reviewed code.

### 5. Type-modeling smells (TS-specific)

- **Stringly-typed unions that should be discriminated unions** — `type` field checked by string instead of a tagged union enabling exhaustiveness.
- **Missing exhaustiveness**: `switch` over a union with no `never`-typed default → silent gaps when the union grows.
- **Enum pitfalls**: numeric enums leaking numbers into the type; consider union of string literals or `as const` objects. (Keep light — team preference.)
- **Overuse of optional (`?`) where a union with an explicit state is clearer** (e.g. `{ loading: true } | { loading: false; data: T }` vs `data?: T`).
- **`Promise` mishandling that types reveal**: floating promises (unawaited `Promise` in a non-returning position), `async` functions whose `Promise` result is asserted away.

### 6. Minor / style (report as Suggestions only)

- Redundant annotations where inference is obvious and correct (`const n: number = 5`).
- `import type` not used for type-only imports (matters for some bundlers/`isolatedModules`).
- `interface` vs `type` inconsistency within a module.

## Severity

- **Critical**: escape hatch hides a genuine type mismatch that can crash or corrupt data at runtime — `as any`/`as unknown as` laundering an incompatible type, a `!` on a genuinely nullable value in a hot path, `@ts-nocheck` on real logic.
- **High**: cast/assertion that hides a fixable type-modeling problem, or `any` that erases checking across a public surface.
- **Medium**: unnecessary-but-harmless assertion/annotation, cast-instead-of-narrowing where a guard is cheap, missing exhaustiveness.
- **Suggestion**: style-level items from checklist §6.

## Output Format

```markdown
## TypeScript Review: {scope}

### Critical (runtime risk hidden by the type system)
- {file}:{line} — {category}: {description}
  **Necessity:** {what you checked — already assignable / tsc still errors / hides upstream type X}
  **Impact:** {what breaks at runtime}
  **Fix:** {remove cast / add guard / correct source type — with code}

### High (type-modeling problems)
- {file}:{line} — {category}: {description}
  **Necessity:** {evidence}
  **Fix:** {solution}

### Medium (unnecessary assertions, narrowing gaps)
- {file}:{line} — {category}: {description} — {suggested change}

### Suggestions
- {style-level items}
```

If `--multi` was used, append one subsection per advisor that responded (titled with the advisor's name as reported by `second-opinion`), then a **Cross-Model Agreement** subsection noting where advisors and the Claude review converge (consensus → higher confidence).

## Examples

**Staged diff with a redundant cast:**
> /review-typescript --staged

Finds `const user = await getUser(id) as User` where `getUser` already returns `User`. Reports Medium, necessity = "already assignable; `tsc --noEmit` passes with the cast removed," fix = delete `as User`.

**Cast hiding a real mismatch:**
> /review-typescript --changed

Finds `return rows as OrderDTO[]` where `rows` is `Record<string, unknown>[]`. Reports High, necessity = "cast is load-bearing but masks that the DB layer returns untyped rows," fix = type the query result or map/validate into `OrderDTO`.

## Troubleshooting

### Too many `as` hits from re-export syntax
**Solution:** `import { x as y }` and `export { a as b }` are not type assertions. Filter them out — only flag `expr as Type` in value positions.

### Can't tell if a cast is needed without the compiler
**Solution:** Run the project's typecheck (`npx tsc --noEmit`, or the `typecheck`/`build` script in `package.json`) with the assertion removed on a scratch copy. No new error → unnecessary. Prefer this over guessing; say so in the finding.

## Notes

- The point is necessity, not presence. Never flag a cast without saying what you checked.
- A cast that's genuinely needed to compile is a signal to fix a *type*, not a thing to accept silently.
- Respect project conventions in CLAUDE.md (some codebases allow `any` in tests or generated code).
- `as const`, definite-assignment `!` for DI, and boundary casts on validated data are legitimate — don't be dogmatic.
