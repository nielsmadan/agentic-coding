---
name: review-comments
description: Review code comments for quality. Flags: --all (entire codebase, uses parallel agents), --staged (git staged files), --changed (git unstaged changes). Default: --staged --changed combined. Use to ensure comments explain "why" not "what".
argument-hint: [--all | --staged | --changed]
---

# Review Comments

Review code comments to ensure they explain "why" not "what".

## Usage

```
/review-comments                      # staged + changed files (default)
/review-comments --staged             # only git staged files
/review-comments --changed            # only unstaged changes
/review-comments --staged --changed   # both explicitly
/review-comments --all                # entire codebase (parallel agents)
```

## Workflow

### Step 1: Parse Flags

From `$ARGUMENTS`, determine scope:

| Flags Present | Scope |
|---------------|-------|
| (none) | `--staged --changed` |
| `--all` | Entire codebase |
| `--staged` | Staged files only |
| `--changed` | Unstaged files only |
| `--staged --changed` | Both |

### Step 2: Get File List

**For --staged:**
```bash
git diff --cached --name-only
```

**For --changed:**
```bash
git diff --name-only
```

**For --all:**
```bash
# Use Glob to find all source files
**/*.{ts,tsx,js,jsx,py,go,java,kt,swift,rs,c,cpp,h,hpp,cs,rb,php}
```

Filter to only source code files (exclude node_modules, build dirs, etc.).

### Step 3: Review Comments

**For --staged/--changed (small file lists):**
Review files directly - read each file and analyze comments.

**For --all (large codebase):**
Split files into batches and spawn parallel sub-agents:

1. Get all source files
2. Split into batches of ~20 files each
3. Spawn sub-agents in parallel using Task tool:

```
Subagent type: general-purpose
Prompt per batch:
---
Review comments in these files for quality issues:
{file_list}

For each file, identify:
1. "What" comments that should be "why" comments
2. Comments that could be replaced with better function/variable names
3. Obvious/redundant comments

Return findings in this format:
## {filename}
- Line {n}: "{comment}" → {suggestion}
---
```

4. Collect and merge results from all agents

### Step 4: Report Findings

```markdown
## Comment Review: {scope}

### Issues Found

#### {filename}
| Line | Current Comment | Issue | Suggestion |
|------|-----------------|-------|------------|
| {n} | "{comment}" | What not Why | {suggestion} |

### Summary
- Files reviewed: {count}
- Issues found: {count}
- Most common issue: {type}
```

## Comment Quality Guidelines

### Good Comments (WHY)
- Explain business logic decisions
- Document performance considerations
- Clarify non-obvious algorithms
- Explain workarounds or edge cases
- Document assumptions or constraints

### Bad Comments (WHAT)
- Describe what the code is doing syntactically
- Restate variable names or method calls
- Explain obvious operations
- Add noise without value

### Better Alternatives
Instead of "what" comments, prefer:
- Extracting functions with descriptive names
- Using meaningful variable names
- Writing self-documenting code

## Examples

### Bad Comment
```python
# Loop through users and check if active
for user in users:
    if user.is_active:
        active_users.append(user)
```

### Good Refactor
```python
active_users = [u for u in users if u.is_active]
# Or extract to: active_users = filter_active_users(users)
```

### Good Comment (when needed)
```python
# Use binary search here because users list is sorted and can exceed 100k items
index = bisect.bisect_left(sorted_users, target_user)
```

## Notes

- For `--all` on large codebases, parallel agents significantly speed up review
- Focus on actionable suggestions, not nitpicks
- If no files match the scope, report "No files to review"
