---
name: read-docs
description: Search and read internal project documentation. Use proactively when needing project-specific patterns, conventions, architecture, or domain knowledge. Searches docs/, README.md, CLAUDE.md, and other .md files. Invoke before planning features, when entering new code areas, or when debugging.
argument-hint: <keywords or topic>
---

# Read Docs

Search internal documentation for project-specific information.

## Usage

```
/read-docs auth                    # Search for auth-related docs
/read-docs database schema         # Search for database/schema docs
/read-docs                         # List available documentation
```

## Search Strategy

1. **Check for docs/ folder** - Primary documentation location
2. **Search filenames** - Glob for keyword matches in file names
3. **Search contents** - Grep for keyword matches in file contents
4. **Prioritize results**:
   - Exact filename match (e.g., "auth" → `docs/auth.md`)
   - Filename contains keyword (e.g., "auth" → `docs/authentication-guide.md`)
   - Content matches (e.g., "auth" mentioned in `docs/architecture.md`)

## Locations Searched

In order of priority:

1. `docs/**/*.md` - Primary documentation
2. `CLAUDE.md` - Project conventions
3. `README.md` - Project overview
4. `*.md` in project root - Other documentation

## Workflow

### With keywords:

1. Search filenames for keyword matches:
   - Glob pattern: `docs/**/*{keyword}*`

2. Search file contents for keyword matches:
   - Grep pattern: `{keyword}` path: `docs/` and root `*.md` files

Read the most relevant matches and summarize findings.

### Without keywords:

List available documentation:
- Glob pattern: `docs/**/*.md`
- Glob pattern: `*.md` (root-level docs)

Present an overview of available documentation.

## Output

Summarize findings:
1. **Documents found** - List with brief description of each
2. **Key information** - Relevant excerpts for the query
3. **Related docs** - Other documents that may be useful

## Examples

**Search internal docs before implementing auth feature:**
> /read-docs auth

Searches `docs/` filenames and contents for auth-related documentation. Finds `docs/auth.md` and references in `docs/architecture.md`, then summarizes relevant patterns, token handling conventions, and any documented gotchas before you start coding.

**Check for documented gotchas before refactor:**
> /read-docs database migration

Searches for migration-related docs and surfaces any documented pitfalls, required steps, or past issues logged in `docs/log/`. Presents key findings so you can avoid known problems during the refactor.

## Troubleshooting

### No docs/ folder found in project
**Solution:** Fall back to searching root-level `.md` files (README.md, CLAUDE.md, CONTRIBUTING.md). If the project has no documentation at all, use `/research-online` for external references or check inline code comments via Grep for conventions.

### Documentation is stale or contradicts code
**Solution:** Trust the code over the documentation when they conflict. Note the discrepancy in your response so the user can update the docs, and verify behavior by reading the actual source files rather than relying on the outdated documentation.

## Notes

- This skill is for internal project docs, not external library docs
- For external library documentation, use `/research-online`
- If no docs/ folder exists, search root .md files only
