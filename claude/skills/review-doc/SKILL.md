---
name: review-doc
description: Review documentation for accuracy and best practices. Default: reviews docs related to current topic/feature from conversation context. Flags: --staged (git staged .md files), --all (entire docs folder, uses parallel agents). Use after implementing features or when documentation may need updates.
argument-hint: [--staged | --all]
---

# Review Doc

Review documentation for accuracy, completeness, and best practices.

## Usage

```
/review-doc              # Docs related to current context (default)
/review-doc --staged     # Only git-staged .md files
/review-doc --all        # Entire docs folder (parallel agents)
```

## Workflow

### Step 1: Determine Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Identify topic from conversation, find related .md files |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` + `README.md` + `CLAUDE.md` |

### Step 2: Get File List

**For default (context-based):**
1. Identify the topic/feature from recent conversation
2. Search for related .md files using Grep with keywords
3. Include: direct matches, parent overview.md, related docs

**For --staged:**
```bash
git diff --cached --name-only -- '*.md'
```

**For --all:**
```bash
find . -name "*.md" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.dart_tool/*" \
  -not -path "*/build/*"
```

### Step 3: Review

**Small scope (≤5 files):** Review directly.

**Large scope (>5 files or --all):** Spawn parallel sub-agents:

```
Subagent type: general-purpose
Prompt per batch:
---
Review these documentation files against the checklist:
{file_list}

Check each file for:
1. No local paths (/Users/, /home/, C:\)
2. No copy-paste duplication (different abstraction levels OK)
3. Accurate content (file paths exist, class names current)
4. Complete (no TODOs, no incomplete sections)
5. Cross-referenced (links to related docs)
6. Gotchas documented

Return findings as:
## {filename}
- **{Issue type}**: {description} (line {n})
---
```

### Step 4: Report Findings

```markdown
## Documentation Review: {scope}

### Critical (fix now)
- {file}:{line} - {issue}

### High Priority (fix soon)
- {file} - {issue}

### Suggestions
- {file} - {improvement}

### Summary
- Files reviewed: {count}
- Issues found: {count}
```

## Documentation Principles

### 1. No Local Paths
- ❌ `/Users/name/projects/app`, `mathfiend/app2`
- ✅ `lib/services/`, `docs/tech/`

### 2. Assume Senior Developer
- Don't explain basic concepts
- Focus on project-specific patterns and WHY decisions were made

### 3. Single Source of Truth (Clarified)

**OK - Different abstraction levels:**
- Overview: "Auth uses JWT tokens with refresh"
- Detailed doc: Full implementation with code samples
- These serve different purposes and are both valuable

**OK - Different audiences:**
- Quick start: "Run `npm start` to begin"
- Architecture doc: Deep dive with diagrams
- A reader may need one or the other

**NOT OK - Copy-paste duplication:**
- Same paragraph verbatim in multiple files
- Identical code examples without linking to canonical source
- This creates maintenance burden and inconsistency risk

**Rule:** Same topic at different depths = OK. Identical text copy-pasted = NOT OK.

### 4. Overview.md in Every Section
- Each `docs/` subdirectory should have `overview.md`
- High-level concepts + links to detailed docs

### 5. Document Gotchas
- Non-obvious behavior
- Common mistakes
- Platform-specific quirks

### 6. Concrete Examples
- Show actual code from the project
- Use relative file paths
- Reference real implementations

### 7. Agent-Optimized Writing
- Clear, actionable, factual
- Short sentences, active voice
- Code blocks with file context

## Review Checklist

- [ ] No local paths (`/Users/`, `/home/`, `C:\`)
- [ ] No verbatim duplication (abstraction differences OK)
- [ ] File paths exist and are correct
- [ ] Class/function names are current
- [ ] Links to related docs work
- [ ] Gotchas documented
- [ ] No incomplete sections or TODOs

## Common Issues

**Local Paths:**
```bash
grep -r "/Users/" docs/ README.md CLAUDE.md 2>/dev/null
grep -r "/home/" docs/ README.md CLAUDE.md 2>/dev/null
```

**Duplication (bad kind):**
- Same paragraph in multiple files
- Identical code blocks (should link instead)

**Inaccurate:**
- File paths that don't exist
- Class names that were renamed
- Outdated version numbers

## Notes

- Default scope is context-aware - reviews docs related to what you just worked on
- Use `--staged` before commits to catch doc issues early
- Use `--all` periodically for comprehensive review
- Sub-agents parallelize large reviews for speed
