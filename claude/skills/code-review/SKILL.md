--
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

If `--multi` flag is present in $ARGUMENTS, also query Gemini and Codex in parallel:

**Gemini** (run from project root, read-only sandbox):
```bash
cd "{project_root}" && gemini -s --approval-mode default "This is a read-only code review. Do not modify any files.

Review the staged changes (git diff --cached) in this repository. Provide a focused code review in 300 words or less covering:
- Potential bugs or edge cases
- Security concerns
- Performance issues
- Architecture/pattern violations"
```

**Codex** (run from project root, read-only sandbox):
```bash
cd "{project_root}" && codex exec -s read-only "This is a read-only code review. Do not modify any files.

Review the staged changes (git diff --cached) in this repository. Provide a focused code review in 300 words or less covering:
- Potential bugs or edge cases
- Security concerns
- Performance issues
- Architecture/pattern violations"
```

### Timeouts

| Advisor | Timeout |
|---------|---------|
| Gemini | 180s |
| Codex | 180s |

### Error Handling
- If one external advisor fails, continue with the other
- External advisor failures should not block the Claude agent results
- Report which advisor(s) failed if applicable

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

---

## Clean Code Principles Reference

**Early Returns / Avoid Deep Nesting:**
```javascript
// BAD: Deep nesting
function process(user) {
  if (user) {
    if (user.isActive) {
      if (user.hasPermission) {
        return doWork(user);
      }
    }
  }
  return null;
}

// GOOD: Guard clauses
function process(user) {
  if (!user) return null;
  if (!user.isActive) return null;
  if (!user.hasPermission) return null;
  return doWork(user);
}
```

**Small Functions:**
```javascript
// BAD: Section comments indicate function does too much
function processOrder(order) {
  // Validate order
  if (!order.items) throw new Error('No items');
  if (!order.customer) throw new Error('No customer');
  // Calculate totals
  let subtotal = 0;
  for (const item of order.items) {
    subtotal += item.price * item.quantity;
  }
  const tax = subtotal * 0.1;
  // Save
  db.orders.save({ ...order, subtotal, tax });
}

// GOOD: Split into focused functions
function processOrder(order) {
  validateOrder(order);
  const totals = calculateTotals(order);
  saveOrder(order, totals);
}
```

**Meaningful Names:**
```javascript
// BAD: Cryptic names
const d = new Date() - u.c;
if (d > 86400000) { ... }

// GOOD: Self-documenting
const millisSinceCreation = Date.now() - user.createdAt;
const ONE_DAY_MS = 24 * 60 * 60 * 1000;
if (millisSinceCreation > ONE_DAY_MS) { ... }
```

**Other principles** (apply judgment):
- **Single Responsibility**: Each function/class should do one thing well
- **DRY**: Extract repeated logic into reusable units
- **KISS**: Prefer simple solutions over clever ones
- **Fail Fast**: Validate inputs early
- **Immutability**: Prefer immutable data where practical
- **Encapsulation**: Hide implementation details

## Functional Programming Preferences

These are preferred patterns, not strict rules. Use judgment—sometimes imperative code is clearer.

**Declarative Over Imperative:**
```javascript
// Imperative (verbose)
const activeUsers = [];
for (const user of users) {
  if (user.isActive) {
    activeUsers.push(user.name);
  }
}

// Declarative (preferred when clear)
const activeUsers = users
  .filter(u => u.isActive)
  .map(u => u.name);
```

**Other preferences:**
- **Minimize Global State**: Prefer passing data explicitly over shared mutable state
- **Pure Functions**: Prefer functions without side effects
- **Avoid Mutation**: Prefer creating new objects over modifying existing ones
- **Compose Small Functions**: Build complex behavior from simple, focused functions

Note: If a `for` loop is more readable or performant, that's fine. The goal is clarity, not dogma.

## Comments Philosophy

- **"Why" over "What"**: Comments should explain *why* something is done, not *what* the code does
- **Code should be self-documenting**: If you need a "what" comment, consider instead:
  - Renaming variables/functions to be more descriptive
  - Extracting a well-named function
  - Simplifying the logic
- **Good comment**: `// Using insertion sort here because n < 10 and it's cache-friendly`
- **Bad comment**: `// Loop through the array and add each item to the result`
- **Avoid comment cruft**: Don't leave commented-out code, TODO comments that will never be addressed, or redundant doc comments

---

For each issue, explain:
1. What the problem is
2. Why it matters
3. How to fix it (with code example if helpful)
