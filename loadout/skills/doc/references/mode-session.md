# Session Mode (`--session`)

**Invocation:** `/doc --session --md <conversation.md> [--report <file>]`

Integrate the durable knowledge from one work session into the project's docs. The
input `--md` file is a rendered conversation (plain markdown of USER/ASSISTANT turns)
— you do NOT read Claude Code `.jsonl` files here.

Extract and place four kinds of knowledge, using the SAME layout and conventions as
`--update`/`--generate` (see `references/principles.md`):

1. **Gotchas** — pitfalls, surprises, "things we ran into" → the `## Gotchas` section of
   the most relevant module/feature doc.
2. **Decision rationale** — why a product/tech decision was made → the `## Why` section.
3. **Behavior changes** — what the session actually changed → refresh the affected
   `## How it works (current state)` sections.
4. **External findings** — what we learned about a *dependency, platform, harness or external
   API* by probing it: a behavior that contradicts its docs, a version-specific quirk, a
   limit we hit → `docs/reference/<subject>.md`. Sessions are the main source of these, and
   the reason the bucket exists: the finding cost an experiment here and will otherwise be
   re-established from scratch next time. Carry the **date and the version probed** across
   from the session, plus how it was probed; if the session only read upstream's docs, that
   is a *documented* claim with a link, not a verified one. Correct-usage conventions for one
   library go to `library-docs` / `library-use` instead.

## Rules

- Find the right target docs via `docs/overview.md` and the existing tree. Prefer
  augmenting existing docs over creating new ones.
- **Never touch `docs/product/`** (owned by `review-product`).
- Only record durable, project-specific knowledge — skip transient chatter and
  anything already documented. It is fine to conclude there is nothing worth adding.
- **Preview** the proposed edits to the user and apply on confirmation. Leave changes
  **uncommitted** (the user commits).
- **Fallback:** if the repo has no `docs/`, write a single `docs/session-harvests/<name>.md`
  (derive `<name>` from the md filename) capturing the same four categories.
- **Report:** if `--report <file>` is given, write the list of doc files you created or
  edited to it, one path per line (repo-relative). If nothing was integrated, write an
  empty file. This is how the caller records what was harvested.
