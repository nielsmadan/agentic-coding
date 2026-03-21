---
name: cld-md-improver
description: Audit and improve CLAUDE.md files in repositories. Use when user asks to "check CLAUDE.md", "audit CLAUDE.md", "update CLAUDE.md", "improve CLAUDE.md", "fix CLAUDE.md", "CLAUDE.md maintenance", or "project memory optimization". Also use when user says "revise CLAUDE.md" or wants to capture session learnings into CLAUDE.md. Do NOT use for general documentation tasks unrelated to CLAUDE.md files.
---

# CLAUDE.md Improver

Audit, evaluate, and improve CLAUDE.md files to ensure Claude Code has optimal project context. Can also capture session learnings into CLAUDE.md.

## Gotchas
- In this repo, `~/.claude/` is symlinked — changes to CLAUDE.md here affect all projects. The skill could propose changes to a committed, shared file without warning about cross-project impact.
- The cross-referencing step ("check if referenced files exist, if commands would work") has no specific checks defined. It can be done superficially, leading to a high quality score that misses stale paths.

## Instructions

### Step 1: Discovery

Find all CLAUDE.md files:

```bash
find . -name "CLAUDE.md" -o -name ".claude.md" -o -name ".claude.local.md" 2>/dev/null | head -50
```

Also check `~/.claude/CLAUDE.md` for global defaults.

| Type | Location | Purpose |
|------|----------|---------|
| Project root | `./CLAUDE.md` | Primary context (shared via git) |
| Local overrides | `./.claude.local.md` | Personal settings (gitignored) |
| Global defaults | `~/.claude/CLAUDE.md` | User-wide defaults |
| Package-specific | `./packages/*/CLAUDE.md` | Module-level context in monorepos |

### Step 2: Quality Assessment

Evaluate each file against six criteria (see `references/quality-criteria.md` for detailed rubrics):

| Criterion | Weight | What to check |
|-----------|--------|---------------|
| Commands/workflows | 20pts | Build/test/deploy commands present? |
| Architecture clarity | 20pts | Can Claude understand codebase structure? |
| Non-obvious patterns | 15pts | Gotchas and quirks documented? |
| Conciseness | 15pts | No verbose or obvious info? |
| Currency | 15pts | Reflects current codebase? |
| Actionability | 15pts | Instructions executable, not vague? |

Grades: A (90-100), B (70-89), C (50-69), D (30-49), F (0-29).

Cross-reference with the actual codebase: check if referenced files exist, if commands would work, if architecture descriptions are accurate.

### Step 3: Output Quality Report

**Always output the report BEFORE making changes.** Format:

```
## CLAUDE.md Quality Report

### Summary
- Files found: X
- Average score: X/100
- Files needing update: X

### File-by-File Assessment

#### 1. ./CLAUDE.md (Project Root)
**Score: XX/100 (Grade: X)**

| Criterion | Score | Notes |
|-----------|-------|-------|
| Commands/workflows | X/20 | ... |
| ... | ... | ... |

**Issues:** [specific problems]
**Recommended additions:** [what should be added]
```

### Step 4: Propose Targeted Updates

After the report, ask for user confirmation before editing.

Follow `references/update-guidelines.md` strictly:
- **Add** only genuinely useful info: discovered commands, gotchas, package relationships, testing approaches, config quirks
- **Avoid** restating what's obvious from code, generic best practices, one-off fixes, verbose explanations
- Show diffs for each proposed change with a brief "why this helps"

Use `references/templates.md` for section formatting guidance.

### Step 5: Apply Updates

After user approval, apply changes with the Edit tool. Preserve existing content structure.

### Alternative: Session Learnings Mode

If invoked at end of session or with "revise CLAUDE.md":

1. **Reflect** on session: what context was missing? Commands discovered? Gotchas encountered? Code style patterns?
2. **Decide placement**: `CLAUDE.md` for team-shared info, `.claude.local.md` for personal preferences
3. **Draft additions** — one line per concept, concise
4. **Show proposed diffs** with "why" for each
5. **Apply with approval** only

### User Tips to Share

- Press `#` during a session to auto-incorporate learnings into CLAUDE.md
- Use `.claude.local.md` for personal preferences (add to `.gitignore`)
- Global defaults go in `~/.claude/CLAUDE.md`
- Keep it concise — CLAUDE.md is part of the prompt

## Examples

### Example 1: Auditing a project

User says: "Check if my CLAUDE.md is up to date"

Actions:
1. Find all CLAUDE.md files in the repo
2. Read each file and cross-reference with codebase (check package.json for commands, verify file paths exist, etc.)
3. Score each file against quality criteria
4. Output quality report showing a score of 45/100 (Grade D) — missing build commands, outdated architecture section referencing deleted `src/legacy/` dir
5. Propose additions: commands table from package.json, updated architecture section, gotcha about required Node 20+
6. After user approves, apply edits

### Example 2: Capturing session learnings

User says: "/claude-md-improver" or "revise CLAUDE.md" at end of session

Actions:
1. Reflect on session — discovered that `npm test -- --runInBand` is needed, found that `src/config.ts` must be imported before any DB calls
2. Draft two additions: testing command note, initialization order gotcha
3. Show diffs targeting `./CLAUDE.md`
4. Apply after approval

## Troubleshooting

### No CLAUDE.md files found
**Cause:** New project or CLAUDE.md not yet created.
**Solution:** Offer to create one using the minimal template from `references/templates.md`. Ask about project type (standard, monorepo, package) to pick the right template.

### Score seems wrong
**Cause:** Assessment may not have cross-referenced enough of the codebase.
**Solution:** Read key files (package.json, main config, CI config) to verify commands and architecture before scoring. Re-run assessment with deeper codebase analysis.

### User rejects proposed changes
**Cause:** Changes may be too generic or not project-specific enough.
**Solution:** Ask what specific areas the user wants improved. Focus on concrete, project-specific additions only.
