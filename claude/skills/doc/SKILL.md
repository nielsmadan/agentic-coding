---
name: doc
description: Documentation review and generation. Modes: --review (check docs against standards, default), --generate (create docs for code). Scope: --staged, --all, or context-based. Use for documentation quality, creation, and maintenance.
argument-hint: [--review | --generate <target>] [--staged | --all]
---

# Doc

Review and generate documentation following consistent principles.

## Usage

```
/doc                              # Review docs related to current context (default)
/doc --review                     # Explicit review mode
/doc --review --staged            # Review staged .md files
/doc --review --all               # Review all docs (parallel agents)
/doc --generate <target>          # Generate docs for file/module/feature
/doc --generate --staged          # Generate docs for staged code changes
```

## Documentation Principles

Both review and generate modes follow these principles. Review checks conformance; generate applies them.

### 1. No Local Paths
- ❌ `/Users/name/projects/app`, `mathfiend/app2`
- ✅ `lib/services/`, `docs/tech/`

### 2. Assume Senior Developer
- Don't explain basic concepts (the framework, the language, etc.)
- Focus on project-specific patterns and WHY decisions were made
- Skip tutorials - show implementation directly

### 3. Single Source of Truth

**OK - Different abstraction levels:**
- Overview: "Auth uses JWT tokens with refresh"
- Detailed doc: Full implementation with code samples

**OK - Different audiences:**
- Quick start: "Run `npm start` to begin"
- Architecture doc: Deep dive with diagrams

**NOT OK - Copy-paste duplication:**
- Same paragraph verbatim in multiple files
- Identical code examples without linking to canonical source

**Rule:** Same topic at different depths = OK. Identical text copy-pasted = NOT OK.

### 4. Overview.md in Every Section
- Each `docs/` subdirectory should have `overview.md`
- High-level concepts + links to detailed docs
- Answers: "What's in this section and which doc do I need?"

### 5. Document Gotchas
- Non-obvious behavior
- Common mistakes and how to avoid them
- Platform-specific quirks
- Things that seem like they should work but don't

### 6. Concrete Examples
- Show actual code from the project
- Use relative file paths
- Reference real implementations: `lib/services/foo.dart:123`

### 7. Agent-Optimized Writing
- Clear, actionable, factual
- Short sentences, active voice
- Code blocks with file context
- Bullet points over paragraphs where appropriate

---

## Review Mode (`--review`)

Default mode. Checks documentation against the principles above.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| (none) | Context-related docs | Find docs related to recent conversation |
| `--staged` | Staged .md files | `git diff --cached --name-only -- '*.md'` |
| `--all` | All documentation | Glob `docs/**/*.md` + `README.md` + `CLAUDE.md` |

### Workflow

1. **Get file list** based on scope
2. **Review** (directly if ≤5 files, parallel sub-agents if more)
3. **Report findings** by priority

### Checklist

**Accuracy:**
- [ ] No local paths (`/Users/`, `/home/`, `C:\`)
- [ ] File paths exist and are correct
- [ ] Class/function names are current
- [ ] Code examples work and match actual implementation
- [ ] Links to related docs work

**Quality:**
- [ ] No verbatim duplication across files
- [ ] Gotchas documented
- [ ] Examples are concrete (not generic placeholders)

**Completeness:**
- [ ] No incomplete sections, placeholders, or TODOs
- [ ] Key interfaces documented (APIs, components, hooks, services, utilities)
- [ ] Missing `overview.md` in doc subdirectories flagged
- [ ] Required sections present (Purpose, Usage, Gotchas for modules)

### Output Format

```markdown
## Documentation Review: {scope}

### Critical (fix now)
- {file}:{line} - {issue}

### High Priority (fix soon)
- {file} - {issue}

### Suggestions
- {file} - {improvement}
```

---

## Generate Mode (`--generate`)

Create documentation for code following the principles above.

### Scope

| Flag | Scope | Method |
|------|-------|--------|
| `<target>` | Specific file/module/feature | Read the code, generate docs |
| `--staged` | Staged code changes | Generate docs for what changed |

### Workflow

1. **Read the code** - Understand what it does, how it works
2. **Check for existing docs** - Update vs create new
3. **Generate documentation** following the principles
4. **Place appropriately** - In `docs/` with proper structure

### What to Document

For a **module/service:**
```markdown
# {Module Name}

## Purpose
{What this module does and why it exists}

## Usage
{How to use it - code examples from the project}

## API
{Key functions/methods with signatures}

## Gotchas
{Non-obvious behavior, common mistakes}

## Related
{Links to related docs}
```

For a **feature:**
```markdown
# {Feature Name}

## Overview
{What the feature does for users}

## Architecture
{How it's implemented - key components}

## Files
{Key files involved with brief descriptions}

## Configuration
{Any config options}

## Gotchas
{Edge cases, limitations, common issues}
```

For **staged changes:**
1. Identify what changed (new feature, modified behavior, etc.)
2. Find or create relevant doc file
3. Update to reflect the changes
4. Ensure gotchas are documented

### Output

Generate docs directly into `docs/` folder with appropriate structure:
- `docs/tech/` for technical implementation
- `docs/features/` for feature documentation
- `docs/api/` for API documentation
- Create `overview.md` in new directories

---

## Notes

- Default is review mode with context-based scope
- Both modes use the same principles - review checks, generate applies
- Use `--staged` before commits to catch issues early
- Use `--all` periodically for comprehensive review
- Sub-agents parallelize large reviews/generations
