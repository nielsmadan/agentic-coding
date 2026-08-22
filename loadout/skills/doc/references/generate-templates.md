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

## Reference Template (`docs/reference/<subject>.md`)

For an **external** subject — a dependency, platform, harness, protocol, or service. See
"External reference" in `principles.md` for when one is warranted.

```markdown
# {Subject}

{One line: what it is and why we build against it.}

## What we verified
{Claims we established ourselves. Each carries the date AND the version probed, plus a
one-line note on how — so the next reader can re-run it.}

- **{Behavior}** — {what happens}. Verified {YYYY-MM-DD} against {name} {version}.
  {The probe, in one line.}

## What upstream documents
{Claims taken from the docs, each with its link. Kept separate from the above: these are
the ones upstream can change without telling us.}

## Gotchas
{Surprises, contradictions with the docs, footguns, things that look supported and aren't.}

## How this affects us
{Only the consequence for this repo — the workaround we adopted, the constraint it puts on
our design. Point at the code (`file:line`); don't restate it.}

## Upstream
- Docs: {url}
- Changelog / releases: {url}
- Relevant issues: {url}
```

Notes:
- For files longer than ~100 lines, add a short table of contents at the top.
- Keep cross-references one level deep — link to a doc, not to a doc that only links onward.
- Reference docs: never mirror upstream — record the delta. And never stamp a verification
  you did not run; an unverified claim is a *documented* one with a link, or it is left out.
