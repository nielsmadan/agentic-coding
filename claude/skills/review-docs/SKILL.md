# Documentation Review Command

Conduct a comprehensive review of all project documentation following agent-first best practices.

## Documentation Principles

Documentation is **primarily for AI coding agents**, secondarily for humans.

### Core Rules

1. **No Local Paths**
   - ❌ Never include absolute paths: `/Users/name/projects/app`
   - ❌ Never include developer-specific paths: `mathfiend/app2`
   - ✅ Use relative paths from project root: `lib/services/`, `docs/tech/`
   - ✅ Use placeholders for examples: `/path/to/project`, `YOUR_USERNAME`

2. **Assume Senior Developer**
   - Don't explain basic concepts (Flutter, Riverpod, Dart, Git, HTTP, etc.)
   - Focus on project-specific patterns and decisions
   - Include WHY decisions were made, not HOW basic technology works
   - Skip tutorials - show implementation directly

3. **Single Source of Truth**
   - No content duplication across docs
   - One canonical document per topic
   - Other docs link to canonical source, don't repeat content
   - Use cross-references liberally

4. **Overview.md in Every Section**
   - Each `docs/` subdirectory must have `overview.md`
   - High-level concepts + links to detailed docs
   - Serves as navigation guide for that section
   - Answers: "What's in this section and which doc do I need?"

5. **Document Gotchas**
   - What trips up coding agents?
   - Non-obvious behavior patterns
   - Common mistakes and how to avoid them
   - Edge cases requiring special handling
   - Things that seem like they should work but don't
   - Platform-specific quirks

6. **Concrete Examples Over Theory**
   - Show actual code from the project
   - Reference real file paths (relative)
   - Link to actual implementations: `lib/services/foo.dart:123`
   - Use project-specific class/function names

7. **Agent-Optimized Writing**
   - Clear, actionable, factual
   - No marketing speak or unnecessary enthusiasm
   - Short sentences, active voice
   - Bullet points over paragraphs where appropriate
   - Code blocks with file context

## Review Process

### 1. Scan All Documentation Files

Find all `.md` files in project (exclude `node_modules`, `.dart_tool`, `build`, `ios/Pods`):

```bash
find . -name "*.md" -type f \
  -not -path "*/node_modules/*" \
  -not -path "*/.dart_tool/*" \
  -not -path "*/build/*" \
  -not -path "*/ios/Pods/*" \
  -not -path "*/.flutter-plugins*"
```

Focus review on:
- `docs/`
- `README.md`
- `CLAUDE.md`
- `AGENTS.md`
- Root-level documentation

### 2. Check Each Doc Against Checklist

For every documentation file:

- [ ] **No local paths**: Search for `/Users/`, `/home/`, `C:\`, absolute paths, `mathfiend/app[0-9]`
- [ ] **No duplication**: Content is unique OR clearly links to canonical source
- [ ] **Accurate**: Matches current codebase
  - File paths exist and are correct
  - Class names, function names are current
  - Code examples are valid
  - Version numbers are accurate
- [ ] **Complete**: Covers stated scope
  - No TODO markers
  - No incomplete sections
  - All promised topics covered
- [ ] **Cross-referenced**: Links to related docs
  - Parent section overview.md linked
  - Related implementation docs linked
  - API docs reference PRD, vice versa
- [ ] **Gotchas documented**: Non-obvious behavior noted
  - Edge cases explained
  - Common mistakes listed
  - Platform differences highlighted
- [ ] **Senior-dev appropriate**: No basic explanations
  - Assumes knowledge of tech stack
  - Focuses on project-specific implementation
  - Shows decisions, not fundamentals
- [ ] **Agent-optimized**: Clear and actionable
  - Factual tone
  - Concrete examples
  - Relative file paths only
  - Cross-references instead of duplication

### 3. Structural Checks

- [ ] Each `docs/` subdirectory has `overview.md`
  - `docs/overview.md` - Top-level documentation map
  - `docs/prd/overview.md` - Product requirements index
  - `docs/tech/overview.md` - Technical documentation index
  - `docs/testing/overview.md` - Testing guides index
  - `docs/design/overview.md` - Design documentation index (if exists)

- [ ] Overview files contain:
  - High-level section purpose
  - List of all docs in section with brief descriptions
  - When to use which doc
  - Common gotchas for that domain

- [ ] Documentation hierarchy is clear:
  - Root README.md → Points to docs/ for details
  - docs/README.md (if exists) → Maps all documentation
  - Section overview.md → Indexes section docs
  - Detailed docs → Cover specific topics

### 4. Common Issues to Find

**Local Paths**:
```bash
# Search patterns
grep -r "/Users/" docs/ README.md CLAUDE.md 2>/dev/null
grep -r "/home/" docs/ README.md CLAUDE.md 2>/dev/null
grep -r "mathfiend/app[0-9]" docs/ README.md CLAUDE.md 2>/dev/null
```

**Duplication**:
- Same architecture explanation in multiple docs
- Button component docs repeated
- API authentication flow described multiple times
- Look for: "as mentioned in...", repeated code blocks, similar section titles

**Inaccurate Content**:
- Check file paths: `lib/foo/bar.dart` - does it exist?
- Check class names: `FooService` - does it exist in codebase?
- Check version numbers: Are they consistent across docs?

**Broken Cross-References**:
- Links to files that don't exist
- References to sections that were moved/renamed
- Missing links to obvious related docs

### 5. Generate Report

Provide findings in this format:

#### CRITICAL ISSUES (Fix Immediately)
- **Local Paths Found**:
  - `README.md:33` - Contains `mathfiend/app2`
  - `docs/tech/setup.md:15` - Contains `/Users/name/projects`

- **Inaccurate Content**:
  - `docs/tech/api.md:45` - References non-existent `lib/services/old_service.dart`
  - `CLAUDE.md:100` - States Flutter 3.5, actually using 3.38

#### HIGH PRIORITY (Fix Soon)
- **Missing Documentation**:
  - `docs/tech/iap.md` - No implementation doc for IAP system
  - `docs/tech/tutorials.md` - Tutorial system undocumented

- **Duplication**:
  - Architecture overview repeated in `README.md` and `docs/tech/overview.md`
  - Button components explained in both `CLAUDE.md` and `docs/design/buttons.md`

- **Missing Cross-References**:
  - `docs/tech/init.md` should link to `docs/tech/login.md` (mentions login flow)
  - `docs/prd/api-integration.md` should link to `docs/prd/checksum.md` (discusses checksums)

#### MEDIUM PRIORITY (Improve Over Time)
- **Missing Overview Files**:
  - `docs/testing/overview.md` doesn't exist
  - `docs/overview.md` doesn't exist

- **Incomplete Sections**:
  - `docs/prd/features.md:45` - Lists 19 problem types but only describes 15
  - `docs/tech/game-engine.md:200` - Missing implementations for several problem types

- **Missing Gotchas**:
  - `docs/tech/persistence.md` - No gotchas about SharedPreferences initialization
  - `docs/tech/api.md` - Missing note about token refresh timing

#### LOW PRIORITY (Nice to Have)
- **Style Improvements**:
  - Inconsistent code block language tags
  - Mixed use of "we" vs passive voice
  - Some overly verbose explanations

### 6. Prioritize Fixes

**Fix Order**:
1. Remove all local paths
2. Fix inaccurate content (broken file paths, wrong class names)
3. Create missing critical docs (IAP, notifications, tutorials if mentioned)
4. Remove duplication via cross-referencing
5. Add missing cross-references
6. Create missing overview.md files
7. Complete incomplete sections
8. Add gotchas to existing docs
9. Style improvements

## Output Format

```markdown
# Documentation Review Report - [DATE]

## Summary
- **Total docs reviewed**: X files
- **Critical issues**: X
- **High priority**: X
- **Medium priority**: X
- **Low priority**: X

## Critical Issues [FIX NOW]

### Local Paths (X found)
- file:line - description
...

### Inaccurate Content (X found)
- file:line - description
...

## High Priority [FIX SOON]

### Missing Documentation (X gaps)
- Topic name - why it's needed
...

### Duplication (X instances)
- Original location → Duplicate locations
...

### Missing Cross-References (X missing)
- From doc → To doc (reason)
...

## Medium Priority

[Similar format]

## Low Priority

[Similar format]

## Recommendations

1. First priority actions
2. Structural improvements
3. Process improvements (e.g., review docs during PRs)

## Files Requiring Changes

- file1.md - [list of changes]
- file2.md - [list of changes]
...
```

## Best Practices Reminder

**Good Documentation**:
- Relative paths: `lib/services/foo_service.dart`
- Senior dev focus: "FooService uses Riverpod for DI"
- Gotchas: "Must initialize before first access or throws"
- Cross-references: "See `docs/tech/api.md` for endpoint details"
- Code examples from actual project

**Bad Documentation**:
- Absolute paths: `/Users/bob/mathfiend/app5/lib/services/foo_service.dart`
- Basic explanations: "Riverpod is a state management library for Flutter..."
- No gotchas: Just happy path
- Duplication: Repeating same content across files
- Generic examples not from project

## After Review

1. Create issues/tasks for critical and high priority items
2. Fix local paths immediately (quick wins)
3. Plan doc creation sprints for missing docs
4. Set up doc review as part of PR process
5. Keep this review command handy - run quarterly or after major changes
