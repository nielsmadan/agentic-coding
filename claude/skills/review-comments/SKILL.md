---
name: review-comments
description: Review and clean up low-quality code comments. Use when you notice "what" comments that should be "why" comments, or want to clean up comment noise before a PR.
argument-hint: [--all | --staged | --changed | --fix]
---

# Review Comments

Review code comments for quality, then offer to fix issues found.

## Flags

- `--staged` - git staged files
- `--changed` - git unstaged changes
- `--all` - entire codebase (parallel agents)
- `--fix` - auto-apply fixes (remove + refactor) without prompting
- Default: `--staged --changed` combined

## Usage

```
/review-comments              # staged + changed (default)
/review-comments --all        # entire codebase
/review-comments --fix        # review and auto-fix
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

### Step 5: Offer to Fix

**If `--fix` flag is present:** Skip the prompt and directly apply Option 2 (Remove and refactor).

**Otherwise**, if issues were found, ask the user:

```
Found {n} low-quality comments. How would you like to proceed?

1. **Remove all** - Delete all flagged comments
2. **Remove and refactor** - Delete comments + extract better function/variable names where suggested
3. **Cherry-pick** - Show me each one and I'll decide
4. **Skip** - Keep the report, don't change anything
```

Based on user choice:

**Option 1 (Remove all):**
- Use Edit tool to remove each flagged comment
- Report: "Removed {n} comments from {m} files"

**Option 2 (Remove and refactor):**
- Remove comments
- Where suggestion was "extract to function" or "rename variable", apply that refactor
- Report changes made

**Option 3 (Cherry-pick):**
- Present each issue one at a time: "Line 42: `// increment counter` - Remove? (y/n/stop)"
- Apply user's choices

**Option 4 (Skip):**
- End without changes

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

## Troubleshooting

### False positives on license headers or necessary comments
**Solution:** License headers and legal notices are required -- skip them during review. If the tool flags doc comments (JSDoc, docstrings) or regulatory annotations, those are intentional and should be excluded from cleanup.

### Comments in unfamiliar language or framework
**Solution:** Focus on structural patterns (e.g., comments restating the next line of code are low-quality in any language). For framework-specific annotations or directives you do not recognize, leave them in place and flag them for manual review rather than removing them.

## Notes

- For `--all` on large codebases, parallel agents significantly speed up review
- Focus on actionable suggestions, not nitpicks
- If no files match the scope, report "No files to review"
