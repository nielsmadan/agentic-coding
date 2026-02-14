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

## Notes

- Focus on commits from the last 3-6 months unless investigating older issues
- Pay attention to refactors, dependency updates, and merge commits
- If a past issue log matches, read it fully - it may contain the solution
