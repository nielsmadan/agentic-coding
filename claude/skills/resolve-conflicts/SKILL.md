---
name: resolve-conflicts
description: Resolve git conflicts from any operation (merge, rebase, cherry-pick, stash, revert). Use when encountering conflicted files during git operations.
argument-hint: [file path]
---

# Resolve Conflicts

Resolve git conflicts from any operation with proper continuation workflow.

## Usage

```
/resolve-conflicts              # Resolve all conflicts
/resolve-conflicts path/to/file # Focus on specific file
```

## Workflow

### Step 1: Detect Operation Type

Use Glob to check for these sentinel files in the `.git/` directory:
- `.git/MERGE_HEAD` → **Merge**
- `.git/rebase-merge` or `.git/rebase-apply` → **Rebase**
- `.git/CHERRY_PICK_HEAD` → **Cherry-pick**
- `.git/REVERT_HEAD` → **Revert**
- None of the above → **Stash** (or manual conflict)

| Operation | Detection | Continue | Abort |
|-----------|-----------|----------|-------|
| Merge | `MERGE_HEAD` exists | `git commit` | `git merge --abort` |
| Rebase | `rebase-merge/` or `rebase-apply/` | `git rebase --continue` | `git rebase --abort` |
| Cherry-pick | `CHERRY_PICK_HEAD` exists | `git cherry-pick --continue` | `git cherry-pick --abort` |
| Revert | `REVERT_HEAD` exists | `git revert --continue` | `git revert --abort` |
| Stash | None of above | `git stash drop` | `git checkout --theirs .` or `git reset --hard` |

### Step 2: List Conflicted Files

```bash
git diff --name-only --diff-filter=U
```

Then run `git status` to see the full conflict status for each file.

Conflict markers in `git status`:
- `UU` - Both modified (most common)
- `AA` - Both added
- `DD` - Both deleted
- `AU`/`UA` - Added by us/them, modified by other
- `DU`/`UD` - Deleted by us/them, modified by other

### Step 3: Analyze Each Conflict

Read the conflicted file and identify:

```
<<<<<<< HEAD (or ours)
Current branch changes
=======
Incoming changes
>>>>>>> branch-name (or theirs)
```

**For rebase conflicts:** "Ours" is the branch being rebased onto, "theirs" is the commit being replayed. This is inverted from merge!

### Step 4: Present Resolution Options

For each conflict, explain:
1. What the current (HEAD) version does
2. What the incoming version does
3. Recommend one of:
   - **Keep current** - incoming change not needed
   - **Keep incoming** - current is outdated
   - **Merge both** - both changes are needed
   - **Rewrite** - neither version is correct as-is

### Step 5: Apply Resolution

Edit the file to:
1. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
2. Keep the correct code
3. Ensure the result is syntactically valid

### Step 6: Mark Resolved and Continue

```bash
# After resolving each file
git add <resolved-file>

# After all files resolved, based on operation type:
# Merge:
git commit

# Rebase:
git rebase --continue

# Cherry-pick:
git cherry-pick --continue

# Revert:
git revert --continue
```

## Output Format

```markdown
## Conflict Resolution: {MERGE|REBASE|CHERRY-PICK|REVERT}

### Situation
- Operation: {type}
- Current branch: {branch}
- Incoming: {branch/commit}

### Conflicted Files ({count})
| File | Type | Complexity |
|------|------|------------|
| {path} | UU | {simple/moderate/complex} |

### {file}

**Current (HEAD):**
```{lang}
{code}
```

**Incoming ({source}):**
```{lang}
{code}
```

**Resolution:** {Keep current | Keep incoming | Merge both}
**Reason:** {explanation}

---

### Next Steps

After all conflicts resolved:
1. `git add {files}`
2. `{continue_command}`

To abort:
- `{abort_command}`
```

## Examples

**Merge conflict on auth logic -- merge both sides:**
> /resolve-conflicts src/auth/session.ts

Detects a merge operation, reads the conflict markers in the session file, and determines that both sides added complementary validation checks. Recommends merging both changes together and produces a clean resolution that includes both validations.

**Rebase conflict with inverted ours/theirs:**
> /resolve-conflicts

Detects a rebase operation and reminds that ours/theirs semantics are inverted during rebase. Walks through each conflicted file, explains what the rebased commit intended versus the target branch state, and resolves accordingly before running `git rebase --continue`.

## Guidelines

- **Understand both sides** before resolving - don't blindly pick one
- **Check for semantic conflicts** - code may compile but logic is broken
- **Review the full file** - changes outside markers may be affected
- **Test after resolving** - run tests if available
- **For rebase:** remember ours/theirs are inverted from merge

## Common Patterns

### Lock File Conflicts (package-lock.json, yarn.lock)

Regenerate rather than manually resolve:
```bash
git checkout --theirs package-lock.json  # or --ours
npm install  # regenerates lock file
git add package-lock.json
```

### Auto-generated Files

Accept one version and regenerate:
```bash
git checkout --theirs <file>
# Run generation command
git add <file>
```

### Both Added Same File Differently

Usually keep one and incorporate changes from other manually.

### Deleted vs Modified

Decide: should file exist or not? If yes, keep modified. If no, remove.
```bash
# Keep the file (accept modification)
git add <file>

# Delete the file
git rm <file>
```
