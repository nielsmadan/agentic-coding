---
name: code-review
description: Code review workflow. Use when reviewing code changes, PRs, or specific files for quality, bugs, and best practices.
argument-hint: <target> [--logic] [--architecture] [--security] [--performance] [--history] [--comments] [--test] [--interface] [--clean-code] [--multi]
---

# Code Review: $ARGUMENTS

Review the code related to: **$ARGUMENTS**

## Usage

```
/code-review                          # All 9 aspects (default)
/code-review <target>                 # All 9 aspects, scoped to target
/code-review --architecture           # Architecture only
/code-review --security --performance # Two aspects
/code-review --logic src/auth/        # One aspect, scoped to target
/code-review --multi                  # All aspects + Gemini + Codex
/code-review --multi --architecture   # Architecture only + Gemini + Codex
```

## Aspect Selection

Aspect flags let you run a subset of the review agents instead of all 9. Flags are additive — pass as many as you want.

| Flag | Maps to |
|------|---------|
| `--logic` | Agent 1: Bug & Logic Review (inline) |
| `--architecture` | Agent 2: Architecture & Patterns Review (inline) |
| `--security` | Agent 3a: Security Review (inline + delegate to `/review-security`) |
| `--performance` | Agent 3b: Performance Review (inline + delegate to `/review-perf`) |
| `--history` | Agent 4: Historical Context Review (inline) |
| `--comments` | Agent 5: Comment Quality (delegates to `/review-comments --staged --changed`) |
| `--test` | Agent 6: Test Quality (delegates to `/test --review --staged`) |
| `--interface` | Agent 7: Interface Design (delegates to `/review-interfaces --staged`) |
| `--clean-code` | Agent 8: Clean Code (delegates to `/review-cleancode --staged`) |

**Rules:**
- No aspect flags → run all 9 agents.
- One or more aspect flags → run only those agents, skip the rest.
- `--multi` composes with any aspect selection.
- The non-flag portion of `$ARGUMENTS` is the review target (e.g. `src/auth/`).

## Gotchas
- Sub-agents that delegate to staged-scope sub-skills (`--security`, `--performance`, `--comments`, `--test`, `--interface`, `--clean-code`) return nothing when no files are staged — the review silently has empty agent results. This applies whether an agent runs as part of the full default set or because its flag was explicitly selected.
- The 80-point confidence threshold silently drops findings. A legitimate 75/100 security issue is filtered out with no trace.

## Step 1: Locate and Read Project Guidelines
First, find and read any CLAUDE.md files in the repository root and relevant directories to understand project-specific conventions and rules.

## Step 2: Identify Relevant Code
Search for and identify all files related to "$ARGUMENTS". Use Glob and Grep to find:
- Direct implementations
- Related tests
- Usages/consumers of this code

## Step 3: Parallel Review Agents

Parse aspect flags from `$ARGUMENTS` (`--logic`, `--architecture`, `--security`, `--performance`, `--history`, `--comments`, `--test`, `--interface`, `--clean-code`). If any are present, launch ONLY the corresponding agents. Otherwise launch all 9 agents. Strip the flags from `$ARGUMENTS` before treating the remainder as the review target.

Launch the selected review perspectives IN PARALLEL:

Each agent should output a list of issues. For each issue, include: what the problem is, where it is (file + line), and why it matters. Do NOT assign confidence scores — scoring happens in a separate pass.

### Agent 1: Bug & Logic Review (`--logic`)
- Look for potential bugs, edge cases, race conditions
- Check null/undefined handling
- Verify error handling completeness
- Look for off-by-one errors

### Agent 2: Architecture & Patterns Review (`--architecture`)
- Check compliance with CLAUDE.md rules
- Search `docs/` for documented patterns related to this code area
- Verify code follows existing codebase patterns

### Agent 3a: Security Review (`--security`)
- Check for injection vulnerabilities (SQL, command, XSS, etc.)
- Verify input validation at trust boundaries
- Look for sensitive data exposure (secrets, PII, tokens in logs)
- Check auth/authz gaps

### Agent 3b: Performance Review (`--performance`)
- Identify performance bottlenecks (N+1 queries, unnecessary loops)
- Check algorithmic complexity
- Check for memory leaks
- Look for expensive work in hot paths

### Agent 4: Historical Context Review (`--history`)
- Use git blame to understand code evolution
- Check for TODO/FIXME comments that need addressing
- Identify code that may be stale or unused

### Agent 5: Comment Quality Review (`--comments`)
Invoke `review-comments --staged --changed` to review comment quality in changed files.
- Identify "what" comments that should be "why" comments
- Flag comments that could be replaced with better naming
- Ensure comments add value, not noise

### Agent 6: Test Quality Review (`--test`)
Invoke `test --review --staged` to review test quality in changed test files.
- Check for missing edge cases and coverage gaps
- Identify brittle or flaky test patterns
- Flag over-mocking and testing implementation instead of behavior
- Ensure tests have meaningful assertions

### Agent 7: Interface Design Review (`--interface`)
Invoke `review-interfaces --staged` to review the design quality of functions, classes, and components.
- Check for pit-of-success violations (multiple ways to do the same thing, easy to misuse)
- Flag poor naming, inconsistent vocabulary, weak types
- Identify over-engineered or YAGNI interfaces
- Check encapsulation and public surface area

### Agent 8: Clean Code Review (`--clean-code`)
Invoke `review-cleancode --staged` to review code against clean code principles.
- Check SOLID principles (SRP, OCP, LSP, ISP, DIP)
- Flag DRY violations, YAGNI, unnecessary complexity (KISS)
- Identify code smells (god classes, long methods, feature envy, primitive obsession, shotgun surgery)
- Check design principles (Law of Demeter, separation of concerns, composition over inheritance)

## Step 3.5: External Advisor Reviews (--multi only)

If `--multi` flag is present in $ARGUMENTS, also get external opinions:

Use the **Skill tool** to invoke `second-opinion --quick` with this prompt:

```
Read-only code review. Review the staged changes (git diff --cached) in this repository. Provide a focused code review in 300 words or less covering: potential bugs or edge cases, security concerns, performance issues, and architecture/pattern violations.
```

**IMPORTANT:** Do NOT proceed to Step 4 until the second-opinion results (both Gemini and Codex) have been fully received. Wait for all background commands to complete and collect their output before continuing. This prevents completion notifications from appearing after the review summary.

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

#### Gemini
{gemini_code_review}

#### Codex
{codex_code_review}

#### Cross-Model Agreement
{note areas where external advisors agree/disagree with Claude agents - highlight consensus issues as higher confidence}

## Examples

**Review staged PR changes with all 9 agents:**
> /code-review

Runs 9 parallel review agents (bug/logic, architecture, security, performance, historical context, comment quality, test quality, interface design, clean code) against staged changes and produces a prioritized list of issues grouped by severity.

**Focused single-aspect review:**
> /code-review --architecture

Runs only the architecture & patterns agent. Use this when you already know which concern you care about and don't want to wait on the other 8 agents or sift through their output. Flags are additive — combine them (e.g. `--security --performance`) to run a handful of aspects without running them all.

**Cross-model consensus review:**
> /code-review --multi

Runs the same 9 Claude agents plus external reviews from Gemini and Codex. The output includes a cross-model agreement section highlighting issues where all models converge, giving higher confidence to consensus findings. `--multi` composes with aspect flags, e.g. `/code-review --multi --architecture`.

For each issue, explain:
1. What the problem is
2. Why it matters
3. How to fix it (with code example if helpful)

## Troubleshooting

### Too many changed files for agents to handle
**Solution:** Narrow the review scope by targeting a specific directory or file pattern (e.g., `/code-review src/auth/`) instead of the entire changeset, or break the PR into smaller, focused reviews.

### Agent returns shallow or redundant findings
**Solution:** Ensure the review target is specific enough to give agents meaningful context; vague targets like "everything" produce generic results. Re-run with a focused target and verify that CLAUDE.md contains project-specific patterns the agents can check against.
