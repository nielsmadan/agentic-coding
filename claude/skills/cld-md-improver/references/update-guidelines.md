# CLAUDE.md Update Guidelines

## Core Principle

Only add information that genuinely helps future sessions. Every line must earn its place.

## What TO Add

1. **Commands/workflows discovered** - saves rediscovery
2. **Gotchas and non-obvious patterns** - prevents repeated debugging
3. **Package relationships** - architecture knowledge not obvious from code
4. **Testing approaches that worked** - establishes patterns
5. **Configuration quirks** - environment-specific knowledge

## What NOT to Add

1. **Obvious code info** - "UserService handles users" (the name says that)
2. **Generic best practices** - "write tests", "use good names" (universal, not project-specific)
3. **One-off fixes** - "fixed bug in commit abc123" (won't recur)
4. **Verbose explanations** - prefer `Auth: JWT with HS256` over a paragraph about JWT

## Validation Checklist

- Each addition is project-specific
- No generic advice or obvious info
- Commands are tested and work
- File paths are accurate
- A new session would find this helpful
- Expressed as concisely as possible
