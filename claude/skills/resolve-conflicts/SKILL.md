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

## Gotchas
- During rebase, ours/theirs semantics are INVERTED. "Ours" is the branch being rebased onto (the target), not your working branch. This causes wrong-direction resolutions if you forget.
- Lock file conflicts (package-lock.json, yarn.lock, Podfile.lock) must NEVER be manually resolved. Delete the lock file and regenerate it — manual merging produces corrupt files.

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

### Step 4: Apply Resolution

Edit the file to:
1. Remove conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`)
2. Keep the correct code
3. Ensure the result is syntactically valid

### Step 5: Complete the Resolution

The user invoked this skill to resolve **and** finish an in-progress git
operation, so complete it yourself:

1. Stage the files you resolved: `git add <resolved-files>`.
2. Run the continue command for the detected operation, using a non-interactive
   flag so no editor opens and hangs:

   | Operation | Continue command |
   |-----------|------------------|
   | Merge | `git commit --no-edit` |
   | Rebase | `GIT_EDITOR=true git rebase --continue` |
   | Cherry-pick | `git cherry-pick --continue --no-edit` |
   | Revert | `git revert --continue --no-edit` |
   | Stash | `git stash drop` |

**Guardrails — do not run these automatically:**
- **Aborts** (`git merge/rebase/cherry-pick/revert --abort`) discard work. If
  resolution isn't viable, stop and tell the user the abort command to run.
- **`git reset --hard`** (the stash abort path) is hard-blocked at the harness
  level — the user must run it themselves.
- If a continue command fails (remaining unmerged paths, a rejected pre-commit
  hook, etc.), surface the error and stop. Do not force it through.

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

### Completion
- Staged: {resolved files}
- Ran: `{continue_command}` → {result}

If resolution wasn't viable, abort manually:
- `{abort_command}`
```

## Examples

**Merge conflict on auth logic -- merge both sides:**
> /resolve-conflicts src/auth/session.ts

Detects a merge operation, reads the conflict markers in the session file, and determines that both sides added complementary validation checks. Recommends merging both changes together and produces a clean resolution that includes both validations.

**Rebase conflict with inverted ours/theirs:**
> /resolve-conflicts

Detects a rebase operation and reminds that ours/theirs semantics are inverted during rebase. Walks through each conflicted file, explains what the rebased commit intended versus the target branch state, resolves the conflicts in the files, stages them, and runs `git add` + `GIT_EDITOR=true git rebase --continue` to finish.

## Guidelines

- **Understand both sides** before resolving - don't blindly pick one
- **Check for semantic conflicts** - code may compile but logic is broken
- **Review the full file** - changes outside markers may be affected
- **Test after resolving** - run tests if available
- **For rebase:** remember ours/theirs are inverted from merge

## Common Patterns

### Lock File Conflicts (package-lock.json, yarn.lock)

Regenerate rather than manually resolve. Run:
```
git checkout --theirs package-lock.json  # or --ours
npm install  # regenerates lock file
git add package-lock.json
```

### Auto-generated Files

Accept one version and regenerate. Run:
```
git checkout --theirs <file>
# Run generation command
git add <file>
```

### Both Added Same File Differently

Usually keep one and incorporate changes from other manually.

### Deleted vs Modified

Decide: should file exist or not? If yes, keep modified. If no, remove. Run the appropriate command:
```
# Keep the file (accept modification)
git add <file>

# Delete the file
git rm <file>
```
