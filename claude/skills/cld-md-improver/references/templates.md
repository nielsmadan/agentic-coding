# CLAUDE.md Templates

## Principles

- **Concise**: One line per concept when possible
- **Actionable**: Commands should be copy-paste ready
- **Project-specific**: Not generic advice
- **Current**: Reflects actual codebase state

## Recommended Sections (use only what's relevant)

### Commands
```markdown
## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |
```

### Architecture
```markdown
## Architecture
```
<root>/
  <dir>/    # <purpose>
```
```

### Key Files
```markdown
## Key Files
- `<path>` - <purpose>
```

### Code Style
```markdown
## Code Style
- <convention>
```

### Environment
```markdown
## Environment
Required:
- `<VAR_NAME>` - <purpose>
Setup:
- <setup step>
```

### Testing
```markdown
## Testing
- `<test command>` - <what it tests>
```

### Gotchas
```markdown
## Gotchas
- <non-obvious thing that causes issues>
```

### Workflow
```markdown
## Workflow
- <when to do X>
```

## Project Templates

### Minimal
```markdown
# <Project Name>
<One-line description>
## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |
## Architecture
```
<structure>
```
## Gotchas
- <gotcha>
```

### Package/Module (monorepo)
```markdown
# <Package Name>
<Purpose>
## Usage
```
<import/usage example>
```
## Key Exports
- `<export>` - <purpose>
## Notes
- <important note>
```

### Monorepo Root
```markdown
# <Monorepo Name>
<Description>
## Packages
| Package | Description | Path |
|---------|-------------|------|
| `<name>` | <purpose> | `<path>` |
## Commands
| Command | Description |
|---------|-------------|
| `<command>` | <description> |
## Cross-Package Patterns
- <shared pattern>
```
