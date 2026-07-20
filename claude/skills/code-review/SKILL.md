---
name: code-review
description: Code review workflow. Use when reviewing code changes, PRs, or specific files for quality, bugs, and best practices.
argument-hint: <target> [--logic] [--architecture] [--security] [--performance] [--history] [--comments] [--test] [--interface] [--clean-code] [--typescript] [--project] [--library-use] [--staged] [--unpushed] [--all] [--changed] [--multi] [--rereview]
---

# Code Review: $ARGUMENTS

Review the code related to: **$ARGUMENTS**

## Usage

```
/code-review                          # All 9 aspects, default scope (staged, or unstaged if nothing staged)
/code-review <target>                 # All 9 aspects, scoped to target (overrides scope flags)
/code-review --architecture           # Architecture only
/code-review --security --performance # Two aspects
/code-review --logic src/auth/        # One aspect, scoped to target
/code-review --typescript             # TypeScript-specific review only
/code-review --project                # Project's own review-project checks only
/code-review --library-use            # Library-usage review only (vs the repo's library-use reference)
/code-review --all                    # Whole repo
/code-review --changed                # Unstaged changes only
/code-review --staged                 # Staged changes only (errors if nothing staged)
/code-review --unpushed               # Files changed across all unpushed commits (errors if nothing unpushed)
/code-review --multi                  # All aspects + external advisors
/code-review --multi --architecture   # Architecture only + external advisors
/code-review --all --multi            # Whole repo + external opinions
/code-review --rereview               # Re-review automatically after fixes are applied
```

`--rereview` composes with any aspect, scope, or `--multi` selection.

## Aspect Selection

Aspect flags let you run a subset of the review agents instead of all 9. Flags are additive — pass as many as you want.

| Flag | Maps to |
|------|---------|
| `--logic` | Agent 1: Bug & Logic Review (inline) |
| `--architecture` | Agent 2: Architecture Review (delegates to `/review-architecture`) |
| `--security` | Agent 3a: Security Review (inline + delegate to `/review-security`) |
| `--performance` | Agent 3b: Performance Review (inline + delegate to `/review-perf`) |
| `--history` | Agent 4: Historical Context Review (inline) |
| `--comments` | Agent 5: Comment Quality (delegates to `/review-comments`) |
| `--test` | Agent 6: Test Quality (delegates to `/test --review`) |
| `--interface` | Agent 7: Interface Design (delegates to `/review-interfaces`) |
| `--clean-code` | Agent 8: Clean Code (delegates to `/review-cleancode`) |

Two further aspects are **conditional add-ons** — in the default (no-aspect-flag) run they are included automatically when they apply; with explicit aspect flags they run only if their own flag is passed (see Step 3b.5 for detection):

| Flag | Maps to |
|------|---------|
| `--typescript` | Agent 9: Language Review — delegates to the matching `review-<language>` skill (e.g. `review-typescript`). Auto-included when the scoped files are TypeScript. |
| `--project` | Agent 10: Project-Specific Review — delegates to the project's own `review-project` skill. Auto-included when that skill exists in the repo. |
| `--library-use` | Agent 11: Library-Use Review — delegates to `review-library-use` (checks code against the repo's `library-use` conventions). Auto-included when the repo has a `library-use` reference. |

**Aspect rules:**
- No aspect flags → run all 9 core agents, **plus** any detected language review, the project review, and the library-use review if present.
- One or more aspect flags → run only those agents, skip the rest. The conditional add-ons run only if `--typescript` / `--project` / `--library-use` (or another `--<language>`) is among the flags.
- `--multi` composes with any aspect selection.
- The non-flag portion of `$ARGUMENTS` is the review target (e.g. `src/auth/`).

### Language & project reviews (plug-and-play)

Language reviews and the project review are the extensible layer on top of the 9 language-agnostic aspects:

- **Language reviews** live globally in `claude/skills/review-<language>/`. They hold checks that apply to *every* project in that language (e.g. `review-typescript` covers judgment-level type design a linter can't decide — type modeling, inference-vs-annotation, casts/`any` that hide a modeling problem; it deliberately does not duplicate typescript-eslint). To add a new language, create a `review-<language>` skill and add a row to the detection registry in Step 3b.5 — `code-review` will auto-route to it. Nothing else to wire.
- **The project review** is a skill the *project* defines at `.claude/skills/review-project/` for issues unique to that one codebase (conventions, gotchas, house rules that don't generalize). `code-review` calls it only when it exists — projects without one are unaffected. Minimal shape:

  ```markdown
  ---
  name: review-project
  description: Project-specific review checks for <this project>.
  argument-hint: [--staged | --unpushed | --changed | --all]
  ---
  # Review Project
  Review the scoped files (accept --staged/--unpushed/--changed/--all or a target)
  against this project's specific rules: <list the project-specific things reviewers
  keep missing>. Output findings as {file}:{line} — {issue} + fix, grouped by severity.
  ```
- **The library-use review** (`review-library-use`, global) checks the scoped code against the repo's `library-use` reference — the version-specific correct-usage conventions for its third-party libraries (generated by the `library-docs` skill). `code-review` auto-includes it when `.claude/skills/library-use/SKILL.md` exists; repos without one are unaffected. It's non-overlapping with the language-agnostic agents: it flags only doc/version-specific library misuse.

## Scope Selection

Scope flags determine *which files* the agents review. The resolved scope is passed through to every delegated sub-agent.

| Flag | Meaning |
|------|---------|
| `--staged` | Review staged changes only (`git diff --cached`). |
| `--unpushed` | Review files changed across unpushed commits only (`git diff <last-pushed>..HEAD`). |
| `--changed` | Review unstaged changes only (`git diff`). |
| `--all` | Review the whole repo (`git ls-files`). |

**Scope rules:**
- Exactly one scope flag may be passed. Multiple → error.
- **Default (no scope flag):** behave as `--staged` if anything is staged; otherwise auto-fall back to `--changed`. Announce the resolved mode at the start of the run so the user isn't surprised. (`--unpushed` is never auto-selected — it's opt-in only.)
- **Explicit `--staged` with nothing staged:** abort immediately with `Nothing staged. Re-run with --all or --changed.` (Explicit ≠ default — no silent fallback.)
- **Explicit `--unpushed` with nothing unpushed:** abort immediately with `Nothing unpushed. Re-run with --staged, --changed, or --all.` If there is no remote/upstream (or the range walks back to the root commit) so the range can't be determined reliably, abort and ask the user to pick another scope. (Explicit ≠ default — no silent fallback.)
- **Target argument wins:** if a non-flag target is provided (e.g. `/code-review src/auth/`), it overrides scope flags entirely. The target is passed to all sub-agents as-is.

## Gotchas
- The 80-point confidence threshold silently drops findings. A legitimate 75/100 security issue is filtered out with no trace.

## Step 1: Locate and Read Project Guidelines
First, find and read any CLAUDE.md files in the repository root and relevant directories to understand project-specific conventions and rules.

## Step 2: Identify Relevant Code
Search for and identify all files related to "$ARGUMENTS". Use Glob and Grep to find:
- Direct implementations
- Related tests
- Usages/consumers of this code

## Step 3: Resolve Scope and Launch Parallel Review Agents

### 3a. Parse flags

Strip aspect flags (`--logic`, `--architecture`, `--security`, `--performance`, `--history`, `--comments`, `--test`, `--interface`, `--clean-code`, `--typescript`, `--project`, `--library-use`), scope flags (`--staged`, `--unpushed`, `--all`, `--changed`), `--multi`, and `--rereview` from `$ARGUMENTS`. The remainder is the review target.

If any aspect flags are present, launch ONLY the corresponding agents (including the conditional add-ons only when `--typescript`/`--project`/`--library-use` is passed). Otherwise launch all 9 core agents plus whatever Step 3b.5 detects.

### 3b. Resolve scope

If a non-flag target was provided, skip this section — pass the target through to every agent as-is.

Otherwise, resolve the scope:

1. If more than one scope flag was passed → error: `Pass only one of --staged, --unpushed, --all, --changed.`
2. If `--staged` was passed explicitly:
   - Run `git diff --cached --name-only`. If empty → abort: `Nothing staged. Re-run with --all or --changed.`
   - Resolved scope: `staged`.
3. If `--unpushed` was passed explicitly:
   - Resolve the range: `git rev-list HEAD --not --remotes` (oldest unpushed commit's parent → HEAD). If empty → abort: `Nothing unpushed. Re-run with --staged, --changed, or --all.` If there is no remote/upstream, or the range walks back to the root commit, abort and ask the user to pick another scope.
   - Resolved scope: `unpushed`.
4. If `--changed` was passed: resolved scope is `changed`.
5. If `--all` was passed: resolved scope is `all`.
6. If no scope flag was passed (default):
   - Run `git diff --cached --name-only`. If non-empty → resolved scope is `staged`.
   - Otherwise → resolved scope is `changed`.
   - Announce the resolution: `No scope flag — defaulting to --staged` or `No scope flag and nothing staged — defaulting to --changed`.

Compute the file list once based on resolved scope:
- `staged` → `git diff --cached --name-only`
- `unpushed` → `git diff --name-only $(git rev-list HEAD --not --remotes | tail -1)^..HEAD`
- `changed` → `git diff --name-only`
- `all` → `git ls-files`

This file list is passed to inline agents and is also used to build the target argument for sub-skills that don't natively support `--changed` (see 3c).

### 3b.5. Detect language & project reviews

Determine which conditional add-on agents apply. Skip this entirely if explicit aspect flags were passed **and** none of them is `--typescript`/`--project`/`--library-use`/another `--<language>` — in that case the user asked for a specific subset and add-ons don't run.

**Language detection registry.** For each language below, it applies if the resolved file list matches its extensions, or (for the `all` scope / when the file list is empty) the repo root has its marker file. If it applies **and** a `review-<language>` skill is installed, include that agent.

| Language | File extensions | Repo marker | Skill |
|---|---|---|---|
| TypeScript | `.ts` `.tsx` `.mts` `.cts` | `tsconfig.json` | `review-typescript` |

*(To add a language: create a `review-<language>` skill and add a row here.)*

**Project review detection.** If the repo defines its own project review skill at `.claude/skills/review-project/SKILL.md`, include the project review agent. If it doesn't exist, skip silently.

**Library-use review detection.** If the repo has a `library-use` reference at `.claude/skills/library-use/SKILL.md`, include the library-use review agent (`review-library-use`). If it doesn't exist, skip silently (suggesting `library-docs` once is fine, but don't block the review).

Announce what got auto-included, e.g. `Detected TypeScript — adding review-typescript`, `Found project review skill — adding review-project`, or `Found library-use reference — adding review-library-use`.

### 3c. Launch agents

Launch the selected review perspectives IN PARALLEL.

Each agent should output a list of issues. For each issue, include: what the problem is, where it is (file + line), and why it matters. Do NOT assign confidence scores — scoring happens in a separate pass.

**Sub-agent invocation pattern.** When a sub-agent delegates to a sub-skill, pass the resolved scope through directly:

| Resolved scope | Argument passed to sub-skill |
|---|---|
| `staged` | `--staged` |
| `unpushed` | `--unpushed` |
| `changed` | `--changed` |
| `all` | `--all` |
| target given | the target itself (e.g. `src/auth/`) |

All delegated sub-skills (`review-architecture`, `review-security`, `review-perf`, `review-comments`, `review-interfaces`, `review-cleancode`, `review-typescript`, `test --review`) accept `--staged | --unpushed | --changed | --all`. No special-casing needed. The project's `review-project` skill is expected to accept the same scope flags (see the minimal shape above) — if it doesn't, pass it the target/file list instead.

Inline agents (no delegation) work directly against the file list computed in step 3b.

### Agent 1: Bug & Logic Review (`--logic`) — inline
Operate on the file list from step 3b.
- Look for potential bugs, edge cases, race conditions
- Check null/undefined handling
- Verify error handling completeness
- Look for off-by-one errors

### Agent 2: Architecture Review (`--architecture`)
Invoke `review-architecture` with the scope-translated arguments per the table above.
- Check layering and module boundary respect
- Flag coupling/cohesion smells (god modules, circular deps, modular mirage, manager centralization)
- Verify pattern consistency with the rest of the system
- Check structural support for stated quality attributes (scalability, resilience, evolvability)
- Flag deviations from `CLAUDE.md`, `docs/`, and ADRs

### Agent 3a: Security Review (`--security`)
Operate on the file list from step 3b. Optionally also invoke `review-security` with the scope-translated arguments per the table above.
- Check for injection vulnerabilities (SQL, command, XSS, etc.)
- Verify input validation at trust boundaries
- Look for sensitive data exposure (secrets, PII, tokens in logs)
- Check auth/authz gaps

### Agent 3b: Performance Review (`--performance`)
Operate on the file list from step 3b. Optionally also invoke `review-perf` with the scope-translated arguments per the table above.
- Identify performance bottlenecks (N+1 queries, unnecessary loops)
- Check algorithmic complexity
- Check for memory leaks
- Look for expensive work in hot paths

### Agent 4: Historical Context Review (`--history`) — inline
Operate on the file list from step 3b.
- Use git blame to understand code evolution
- Check for TODO/FIXME comments that need addressing
- Identify code that may be stale or unused

### Agent 5: Comment Quality Review (`--comments`)
Invoke `review-comments` with the scope-translated arguments per the table above.
- Identify "what" comments that should be "why" comments
- Flag comments that could be replaced with better naming
- Ensure comments add value, not noise

### Agent 6: Test Quality Review (`--test`)
Invoke `test --review` with the scope-translated arguments per the table above.
- Check for missing edge cases and coverage gaps
- Identify brittle or flaky test patterns
- Flag over-mocking and testing implementation instead of behavior
- Ensure tests have meaningful assertions

### Agent 7: Interface Design Review (`--interface`)
Invoke `review-interfaces` with the scope-translated arguments per the table above.
- Check for pit-of-success violations (multiple ways to do the same thing, easy to misuse)
- Flag poor naming, inconsistent vocabulary, weak types
- Identify over-engineered or YAGNI interfaces
- Check encapsulation and public surface area

### Agent 8: Clean Code Review (`--clean-code`)
Invoke `review-cleancode` with the scope-translated arguments per the table above.
- Check SOLID principles (SRP, OCP, LSP, ISP, DIP)
- Flag DRY violations, YAGNI, unnecessary complexity (KISS)
- Identify code smells (god classes, long methods, feature envy, primitive obsession, shotgun surgery)
- Check design principles (Law of Demeter, separation of concerns, composition over inheritance)

### Agent 9: Language Review (`--typescript` / other `--<language>`) — conditional
Only if Step 3b.5 detected a language (or the flag was passed explicitly). For each applicable language, invoke its `review-<language>` skill with the scope-translated arguments per the table above.
- TypeScript → `review-typescript`: judgment-level type design a linter can't decide — type modeling (make invalid states unrepresentable, unions of interfaces, outputs no wider than needed), inference-vs-annotation calls, and casts/`any` that compile but hide a wrong upstream type or unvalidated boundary data. Deliberately non-overlapping with typescript-eslint.

### Agent 10: Project-Specific Review (`--project`) — conditional
Only if Step 3b.5 found a `review-project` skill in the repo (or the flag was passed explicitly). Invoke the project's `review-project` skill with the scope-translated arguments per the table above. This agent checks issues unique to this codebase that the language-agnostic and language-specific agents don't know about.

### Agent 11: Library-Use Review (`--library-use`) — conditional
Only if Step 3b.5 found a `library-use` reference in the repo (or the flag was passed explicitly). Invoke `review-library-use` with the scope-translated arguments per the table above. This agent checks the scoped code against the repo's documented, version-specific library conventions (stale/renamed APIs, deprecated patterns, missing required setup) — non-overlapping with the language-agnostic and language-specific agents.

## Step 3.5: External Advisor Reviews (--multi only)

If `--multi` flag is present in $ARGUMENTS, also get external opinions:

Use the **Skill tool** to invoke `second-opinion --quick`, which queries every external advisor it has configured, in parallel. (The advisor roster lives in the `second-opinion` skill — don't enumerate it here.) Phrase the prompt according to the resolved scope from step 3b:

- `staged` → "Review the staged changes (`git diff --cached`) in this repository."
- `unpushed` → "Review the changes across all unpushed commits (`git diff` against the last pushed commit) in this repository."
- `changed` → "Review the unstaged changes (`git diff`) in this repository."
- `all` → "Review the codebase in this repository as a whole."
- target given → "Review the following target in this repository: `<target>`."

Then append: "Provide a focused code review in 300 words or less covering: potential bugs or edge cases, security concerns, performance issues, and architecture/pattern violations."

**IMPORTANT:** Do NOT proceed to Step 4 until the second-opinion results have been fully received. Wait for all background commands to complete and collect their output before continuing. This prevents completion notifications from appearing after the review summary. If an advisor is missing or errors out, continue with whichever responded — don't drop the others.

## Step 4: Independent Confidence Scoring

Collect all issues from the review agents. Then launch **parallel scorer agents** — one per issue (or batch small groups if there are many). Each scorer receives:
- The issue description and location
- The relevant code context (read the file around the reported lines)
- The CLAUDE.md guidelines

Each scorer independently assigns a confidence score 0-100:
- **0**: False positive, not a real issue
- **25**: Might be real but unlikely
- **50**: Plausible but minor or uncertain
- **75**: Likely real and worth noting
- **100**: Certain, clear problem

The scorer should NOT know which agent found the issue. It evaluates purely based on the code and the claim.

**Filter**: Only issues scoring >= 80 pass through to the output.

## Step 5: Format Output

Only include sections with findings from the agents that actually ran. If an aspect was not selected, omit it — do not render an empty section.

### Critical Issues (Must Fix)
[List issues that could cause bugs, security vulnerabilities, or data loss]

### Improvements (Should Fix)
[List issues that violate patterns, reduce maintainability, or hurt performance]

### Suggestions (Nice to Have)
[List minor style issues, potential refactors, or enhancements]

### External Advisor Reviews (--multi only)

If `--multi` was used, add one subsection per advisor that responded, titled with the advisor's name as reported by `second-opinion`:

#### {advisor name}
{that advisor's review}

#### Cross-Model Agreement
{note areas where the external advisors agree/disagree with the Claude agents - highlight consensus issues (flagged by multiple models) as higher confidence}

## Step 6: Offer to Fix

After presenting the review output, if there are any **Critical** or **Should Fix** findings, use the **AskUserQuestion tool** to let the user pick a fix scope instead of typing one out. This saves the user from describing which issues to address.

Build the options list from what findings actually exist:

- If there are Critical findings → include **"Fix Critical only"** (fixes the `Critical Issues (Must Fix)` section).
- If there are both Critical and Should Fix findings → also include **"Fix Critical + Should Fix"** (fixes Critical and `Improvements (Should Fix)`).
- If there are Should Fix findings but no Critical findings → include **"Fix Should Fix"** instead.
- Always include **"Don't fix anything"** as the last option.

List the strongest/most-inclusive fix option first. Skip this step entirely (no prompt) when there are no Critical and no Should Fix findings — there is nothing actionable to offer.

When the user selects a fix option, apply the fixes for exactly the chosen severity tier(s). `Suggestions (Nice to Have)` are never auto-fixed — mention the user can request those separately if they want them.

## Step 7: Re-Review After Fixes (`--rereview` only)

If `--rereview` was passed AND fixes were applied in Step 6, automatically run the review again to verify the fixes landed cleanly and didn't introduce new issues:

- Re-run Steps 3–6 with the **same aspect, `--multi`, and target/scope selection** as the original run.
- Review the **same file list** computed in step 3b — fixes turn staged files into unstaged edits, so re-resolving scope from scratch could miss them. Reuse the original file list directly rather than recomputing from `git diff`.
- Announce the re-review at the start, e.g. `Re-reviewing after fixes (--rereview)`.
- The re-review's Step 6 fix prompt runs as normal. This forms a natural loop: review → fix → re-review → fix … It terminates when the re-review surfaces no Critical/Should Fix findings (Step 6 is skipped) or the user picks "Don't fix anything".

Without `--rereview`, Step 6 ends the run after fixes are applied — the user must invoke `/code-review` again manually to verify.

## Examples

**Review the default scope with all 9 agents:**
> /code-review

Runs 9 parallel review agents (bug/logic, architecture, security, performance, historical context, comment quality, test quality, interface design, clean code) against staged changes (or unstaged changes if nothing is staged) and produces a prioritized list of issues grouped by severity.

**Focused single-aspect review:**
> /code-review --architecture

Runs only the architecture & patterns agent. Use this when you already know which concern you care about and don't want to wait on the other 8 agents or sift through their output. Flags are additive — combine them (e.g. `--security --performance`) to run a handful of aspects without running them all.

**Whole-repo review:**
> /code-review --all

Runs all 9 agents against every file in the repo (`git ls-files`). Use this for a fresh audit of an unfamiliar project, before a major release, or when nothing in the working tree is changed. Composes with aspect flags and `--multi`, e.g. `/code-review --all --architecture --multi`.

**Cross-model consensus review:**
> /code-review --multi

Runs the same 9 Claude agents plus external reviews from every advisor `second-opinion` has configured. The output includes a cross-model agreement section highlighting issues where the Claude agents and the external advisors converge, giving higher confidence to consensus findings. `--multi` composes with aspect and scope flags, e.g. `/code-review --multi --architecture` or `/code-review --all --multi`.

**Review, fix, then re-review automatically:**
> /code-review --rereview

Runs the review, offers the fix prompt (Step 6), and — once fixes are applied — immediately re-runs the same review on the same files to confirm the fixes landed and introduced no new issues. The loop continues until a re-review comes back with no Critical/Should Fix findings or the user declines to fix. Composes with aspect, scope, and `--multi` flags.

For each issue, explain:
1. What the problem is
2. Why it matters
3. How to fix it (with code example if helpful)

## Troubleshooting

### Too many changed files for agents to handle
**Solution:** Narrow the review scope by targeting a specific directory or file pattern (e.g., `/code-review src/auth/`) instead of the entire changeset, or break the PR into smaller, focused reviews.

### Agent returns shallow or redundant findings
**Solution:** Ensure the review target is specific enough to give agents meaningful context; vague targets like "everything" produce generic results. Re-run with a focused target and verify that CLAUDE.md contains project-specific patterns the agents can check against.
