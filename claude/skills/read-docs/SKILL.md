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

## Notes

- This skill is for internal project docs, not external library docs
- For external library documentation, use `/research-online`
- If no docs/ folder exists, search root .md files only
