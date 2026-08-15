# Documentation Templates

Each doc separates **how it works now** (current-state — `--update` rewrites this
as code changes) from a short **why** (decisions/rationale — rarely touched). Don't
restate code: reference signatures by `file:line` and capture what the agent can't
derive by reading the source.

## Module/Service Template

```markdown
# {Module Name}

## Purpose
{What this module does and why it exists — 1-3 sentences}

## How it works (current state)
{How it behaves now: the flow, key responsibilities, how callers use it.
Reference the code as canonical — do NOT paste signatures.}

## Key entry points
- `lib/services/foo.dart:42` — {what this is, its contract / when to call it}
- `lib/services/foo.dart:88` — {…}

## Gotchas
{Non-obvious behavior, common mistakes, platform quirks}

## Why
{Only non-obvious decisions: why this approach over the alternative. Omit if none.}

## Related
{Links to related docs}
```

## Feature Template

```markdown
# {Feature Name}

## Overview
{What the feature does for users — 1-3 sentences}

## How it works (current state)
{The implementation as it stands now: key components and how they fit together.}

## Key entry points
- `lib/features/x/…:NN` — {role of this file}

## Configuration
{Config options that affect behavior, if any}

## Gotchas
{Edge cases, limitations, common issues}

## Why
{Only non-obvious decisions/tradeoffs. Omit if none.}
```

Notes:
- For files longer than ~100 lines, add a short table of contents at the top.
- Keep cross-references one level deep — link to a doc, not to a doc that only links onward.
