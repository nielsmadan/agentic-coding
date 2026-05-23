---
name: code-review
description: Code review workflow. Use when reviewing code changes, PRs, or specific files for quality, bugs, and best practices.
argument-hint: <target> [--logic] [--architecture] [--security] [--performance] [--history] [--comments] [--test] [--interface] [--clean-code] [--staged] [--all] [--changed] [--multi] [--rereview]
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
/code-review --all                    # Whole repo
/code-review --changed                # Unstaged changes only
/code-review --staged                 # Staged changes only (errors if nothing staged)
/code-review --multi                  # All aspects + Codex
/code-review --multi --architecture   # Architecture only + Codex
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

**Aspect rules:**
- No aspect flags → run all 9 agents.
- One or more aspect flags → run only those agents, skip the rest.
- `--multi` composes with any aspect selection.
- The non-flag portion of `$ARGUMENTS` is the review target (e.g. `src/auth/`).

## Scope Selection

Scope flags determine *which files* the agents review. The resolved scope is passed through to every delegated sub-agent.

| Flag | Meaning |
|------|---------|
| `--staged` | Review staged changes only (`git diff --cached`). |
| `--changed` | Review unstaged changes only (`git diff`). |
| `--all` | Review the whole repo (`git ls-files`). |

**Scope rules:**
- Exactly one scope flag may be passed. Multiple → error.
- **Default (no scope flag):** behave as `--staged` if anything is staged; otherwise auto-fall back to `--changed`. Announce the resolved mode at the start of the run so the user isn't surprised.
- **Explicit `--staged` with nothing staged:** abort immediately with `Nothing staged. Re-run with --all or --changed.` (Explicit ≠ default — no silent fallback.)
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

Strip aspect flags (`--logic`, `--architecture`, `--security`, `--performance`, `--history`, `--comments`, `--test`, `--interface`, `--clean-code`), scope flags (`--staged`, `--all`, `--changed`), `--multi`, and `--rereview` from `$ARGUMENTS`. The remainder is the review target.

If any aspect flags are present, launch ONLY the corresponding agents. Otherwise launch all 9 agents.

### 3b. Resolve scope

If a non-flag target was provided, skip this section — pass the target through to every agent as-is.

Otherwise, resolve the scope:

1. If more than one scope flag was passed → error: `Pass only one of --staged, --all, --changed.`
2. If `--staged` was passed explicitly:
   - Run `git diff --cached --name-only`. If empty → abort: `Nothing staged. Re-run with --all or --changed.`
   - Resolved scope: `staged`.
3. If `--changed` was passed: resolved scope is `changed`.
4. If `--all` was passed: resolved scope is `all`.
5. If no scope flag was passed (default):
   - Run `git diff --cached --name-only`. If non-empty → resolved scope is `staged`.
   - Otherwise → resolved scope is `changed`.
   - Announce the resolution: `No scope flag — defaulting to --staged` or `No scope flag and nothing staged — defaulting to --changed`.

Compute the file list once based on resolved scope:
- `staged` → `git diff --cached --name-only`
- `changed` → `git diff --name-only`
- `all` → `git ls-files`

This file list is passed to inline agents and is also used to build the target argument for sub-skills that don't natively support `--changed` (see 3c).

### 3c. Launch agents

Launch the selected review perspectives IN PARALLEL.

Each agent should output a list of issues. For each issue, include: what the problem is, where it is (file + line), and why it matters. Do NOT assign confidence scores — scoring happens in a separate pass.

**Sub-agent invocation pattern.** When a sub-agent delegates to a sub-skill, pass the resolved scope through directly:

| Resolved scope | Argument passed to sub-skill |
|---|---|
| `staged` | `--staged` |
| `changed` | `--changed` |
| `all` | `--all` |
| target given | the target itself (e.g. `src/auth/`) |

All delegated sub-skills (`review-architecture`, `review-security`, `review-perf`, `review-comments`, `review-interfaces`, `review-cleancode`, `test --review`) accept `--staged | --changed | --all`. No special-casing needed.

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

## Step 3.5: External Advisor Reviews (--multi only)

If `--multi` flag is present in $ARGUMENTS, also get external opinions:

Use the **Skill tool** to invoke `second-opinion --quick`. Phrase the prompt according to the resolved scope from step 3b:

- `staged` → "Review the staged changes (`git diff --cached`) in this repository."
- `changed` → "Review the unstaged changes (`git diff`) in this repository."
- `all` → "Review the codebase in this repository as a whole."
- target given → "Review the following target in this repository: `<target>`."

Then append: "Provide a focused code review in 300 words or less covering: potential bugs or edge cases, security concerns, performance issues, and architecture/pattern violations."

**IMPORTANT:** Do NOT proceed to Step 4 until the second-opinion result (Codex) has been fully received. Wait for all background commands to complete and collect their output before continuing. This prevents completion notifications from appearing after the review summary.

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

If `--multi` was used, include:

#### Codex
{codex_code_review}

#### Cross-Model Agreement
{note areas where Codex agrees/disagrees with Claude agents - highlight consensus issues as higher confidence}

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

Runs the same 9 Claude agents plus an external review from Codex. The output includes a cross-model agreement section highlighting issues where both Claude agents and Codex converge, giving higher confidence to consensus findings. `--multi` composes with aspect and scope flags, e.g. `/code-review --multi --architecture` or `/code-review --all --multi`.

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
