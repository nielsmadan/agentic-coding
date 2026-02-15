---
name: code-review
description: Code review workflow. Use when reviewing code changes, PRs, or specific files for quality, bugs, and best practices.
argument-hint: <target> [--multi]
---

# Code Review: $ARGUMENTS

Review the code related to: **$ARGUMENTS**

## Usage

```
/code-review <target>           # Claude-only review (6 parallel agents)
/code-review --multi <target>   # Also get reviews from Gemini and Codex
```

## Step 1: Locate and Read Project Guidelines
First, find and read any CLAUDE.md files in the repository root and relevant directories to understand project-specific conventions and rules.

## Step 2: Identify Relevant Code
Search for and identify all files related to "$ARGUMENTS". Use Glob and Grep to find:
- Direct implementations
- Related tests
- Usages/consumers of this code

## Step 3: Parallel Review Agents
Launch the following review perspectives IN PARALLEL:

### Agent 1: Bug & Logic Review
- Look for potential bugs, edge cases, race conditions
- Check null/undefined handling
- Verify error handling completeness
- Look for off-by-one errors

### Agent 2: Architecture & Patterns Review
- Check compliance with CLAUDE.md rules
- Search `docs/` for documented patterns related to this code area
- Verify code follows existing codebase patterns
- Assess separation of concerns
- Identify code duplication

### Agent 3: Security & Performance Review
- Check for injection vulnerabilities
- Verify input validation
- Look for sensitive data exposure
- Identify performance bottlenecks (N+1 queries, unnecessary loops)
- Check for memory leaks

### Agent 4: Historical Context Review
- Use git blame to understand code evolution
- Check for TODO/FIXME comments that need addressing
- Identify code that may be stale or unused

### Agent 5: Comment Quality Review
Invoke `/review-comments --staged --changed` to review comment quality in changed files.
- Identify "what" comments that should be "why" comments
- Flag comments that could be replaced with better naming
- Ensure comments add value, not noise

### Agent 6: Test Quality Review
Invoke `/test --review --staged` to review test quality in changed test files.
- Check for missing edge cases and coverage gaps
- Identify brittle or flaky test patterns
- Flag over-mocking and testing implementation instead of behavior
- Ensure tests have meaningful assertions

## Step 3.5: External Advisor Reviews (--multi only)

If `--multi` flag is present in $ARGUMENTS, also get external opinions:

Use the **Skill tool** to invoke `second-opinion --quick` with this prompt:

```
Read-only code review. Review the staged changes (git diff --cached) in this repository. Provide a focused code review in 300 words or less covering: potential bugs or edge cases, security concerns, performance issues, and architecture/pattern violations.
```

## Step 4: Score and Filter Issues
For each issue found, assign a confidence score (0-100).
Only report issues with confidence >= 80.

## Step 5: Format Output

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

**Review staged PR changes with 6 agents:**
> /code-review

Runs 6 parallel review agents (bug/logic, architecture, security/performance, historical context, comment quality, test quality) against staged changes and produces a prioritized list of issues grouped by severity.

**Cross-model consensus review:**
> /code-review --multi

Runs the same 6 Claude agents plus external reviews from Gemini and Codex. The output includes a cross-model agreement section highlighting issues where all models converge, giving higher confidence to consensus findings.

---

Review agents should apply [clean code principles](references/clean-code.md) when evaluating code quality.

For each issue, explain:
1. What the problem is
2. Why it matters
3. How to fix it (with code example if helpful)

## Troubleshooting

### Too many changed files for agents to handle
**Solution:** Narrow the review scope by targeting a specific directory or file pattern (e.g., `/code-review src/auth/`) instead of the entire changeset, or break the PR into smaller, focused reviews.

### Agent returns shallow or redundant findings
**Solution:** Ensure the review target is specific enough to give agents meaningful context; vague targets like "everything" produce generic results. Re-run with a focused target and verify that CLAUDE.md contains project-specific patterns the agents can check against.
