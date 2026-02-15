---
name: review-history
description: Analyze how code changed over time. Use when investigating regressions, understanding why code was written a certain way, or finding when a behavior changed.
argument-hint: <file, function, or feature area>
---

# Review History

Investigate how code evolved over time to understand current behavior or find regressions.

## Usage

```
/review-history src/auth/login.ts
/review-history the authentication flow
/review-history UserProfile component
```

## Workflow

### Step 1: Identify Target Files

From the provided topic, identify the relevant files:
- If a file path is given, use it directly
- If a feature/function name, use Grep/Glob to find relevant files

### Step 2: Git History Analysis

Run these in parallel:

**Recent commits touching the area:**
```bash
git log --oneline -20 -- <file_or_directory>
```

**Detailed blame for key sections:**
```bash
git blame <file> | head -100
```

**Find when specific code was introduced:**
```bash
git log -S "<search_term>" --oneline -- <file>
```

**Check for recent refactors:**
```bash
git log --oneline --since="3 months ago" -- <file_or_directory>
```

### Step 3: Search Past Issue Logs

Check if this problem occurred before:

1. List past issue logs:
   - Glob pattern: `docs/log/*.md`

2. Search logs for relevant keywords:
   - Grep pattern: `{keywords}` path: `docs/log/`

Look for:
- Similar error messages
- Same file/function names
- Related symptoms

### Step 4: Synthesize Findings

Report:

```markdown
## History Analysis: {target}

### Recent Changes
| Date | Commit | Author | Summary |
|------|--------|--------|---------|
| {date} | {hash} | {author} | {message} |

### Key Code Introduction
- `{function/feature}` introduced in {commit} on {date}
- Last modified: {commit} by {author}

### Related Past Issues
{any matching docs/log entries, or "None found"}

### Regression Risk
{assessment: was this working before? when did it break?}
```

## Examples

**Trace when a payment bug was introduced:**
> /review-history processPayment

Uses `git log -S` and `git blame` to trace the payment processing function, identifies the commit that changed the rounding logic three weeks ago, and cross-references with past issue logs to confirm this is when the billing discrepancy started.

**Understand why validation works a certain way:**
> /review-history src/validators/address.ts

Analyzes the git history of the address validator, surfaces the original commit that added the unusual postal code regex along with its commit message explaining a partner API requirement, and checks past issue logs for related context.

## Troubleshooting

### Relevant commit was squashed or rebased away
**Solution:** Use `git reflog` to find the original commit before the squash or rebase. If the reflog has expired, search for the change using `git log -S "<code_snippet>" --all` to locate it in any branch or dangling commit.

### History is too large to analyze effectively
**Solution:** Narrow the scope by passing a specific file path or function name instead of a broad directory. Use `--since` with `git log` to limit the time window, or focus on a single author's contributions with `--author`.

## Notes

- Focus on commits from the last 3-6 months unless investigating older issues
- Pay attention to refactors, dependency updates, and merge commits
- If a past issue log matches, read it fully - it may contain the solution
