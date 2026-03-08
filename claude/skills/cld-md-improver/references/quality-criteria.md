# CLAUDE.md Quality Criteria

## Scoring Rubric

### 1. Commands/Workflows (20 points)

- **20**: All essential commands (build, test, lint, deploy, dev) documented with context
- **15**: Most commands present, some missing context
- **10**: Basic commands only, no workflow
- **5**: Few commands, many missing
- **0**: No commands documented

### 2. Architecture Clarity (20 points)

- **20**: Key directories explained, module relationships documented, entry points identified
- **15**: Good structure overview, minor gaps
- **10**: Basic directory listing only
- **5**: Vague or incomplete
- **0**: No architecture info

### 3. Non-Obvious Patterns (15 points)

- **15**: Gotchas, quirks, workarounds, edge cases, "why we do it this way" documented
- **10**: Some patterns documented
- **5**: Minimal pattern documentation
- **0**: No patterns or gotchas

### 4. Conciseness (15 points)

- **15**: Dense, valuable content; no filler or obvious info; no redundancy with code
- **10**: Mostly concise, some padding
- **5**: Verbose in places
- **0**: Mostly filler or restates obvious code

### 5. Currency (15 points)

- **15**: Reflects current codebase; commands work; file references accurate; tech stack current
- **10**: Mostly current, minor staleness
- **5**: Several outdated references
- **0**: Severely outdated

### 6. Actionability (15 points)

- **15**: Commands can be copy-pasted; steps are concrete; paths are real
- **10**: Mostly actionable
- **5**: Some vague instructions
- **0**: Vague or theoretical

## Red Flags

- Commands that would fail (wrong paths, missing deps)
- References to deleted files/folders
- Outdated tech versions
- Copy-paste from templates without customization
- Generic advice not specific to the project
- "TODO" items never completed
- Duplicate info across multiple CLAUDE.md files
