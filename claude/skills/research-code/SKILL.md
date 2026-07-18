---
name: research-code
description: Research a programming topic online — libraries, best practices, errors, post-cutoff docs. For non-programming topics use `research-general`.
argument-hint: <topic or error message>
---

# Research Code

Research a programming topic from multiple angles using parallel sub-agents, with critical evaluation of source credibility.

## Usage

```
research-code <library> <what you want to do>
research-code "<error message>" <library>
research-code how to implement auth in react-navigation v7
research-code Redux vs Zustand for large app
```

## Gotchas
- Context7 docs may lag behind a recent major release. Check which version is documented before citing it as authoritative.
- "Prefer recent, then higher authority" can be wrong: an authoritative maintainer comment from 18 months ago may be more correct than a popular blog post from last month. Weigh authority first for stable libraries.
- Quick mode may miss nuance. If a "simple" question turns out complex (e.g., "default port" depends on framework integration), note it and suggest re-running in Standard mode.
- GitHub star counts are trivially inflated (~6M suspected fake stars as of 2024) — never cite a star count as evidence of quality, adoption, or trust without vetting it. See `references/fake-stars.md`.

## Workflow

### Step 1: Parse Input

Extract: **library/framework**, **error message** (if any, usually quoted), **version**, **goal/intent**, **problem description** (debugging), **comparison targets** (if "X vs Y").

### Step 2: Classify Query Depth

| Mode | When | Behavior |
|------|------|----------|
| **Quick** | Simple factual lookup, single API question, "what version supports X", "how to do X" with well-known library | Skip internal docs check. Spawn only Docs + General. Skip follow-up loop and critique. |
| **Standard** | Comparisons, best practices, errors, complex implementation, "real world experience", debugging | Full workflow including follow-up loop and adversarial critique |

When in doubt, use Standard.

### Step 3: Check Internal Documentation First (Standard only)

Before external research, Grep relevant keywords in `docs/` and `*.md`. Internal docs often contain project-specific decisions external research won't cover. If found, include in the synthesis.

### Step 4: Spawn Agents in Parallel

Pick the relevant agents and spawn them in a **single Task message** (parallel execution, `subagent_type: general-purpose`). Each captures source metadata: URL, date, source type, and (for community sources) engagement signals.

| Agent | Spawn when | Search strategy |
|-------|------------|-----------------|
| **Docs** | Library/framework mentioned | Context7 `resolve-library-id` then `query-docs`. Fall back to `{lib} official documentation {goal}`. |
| **GitHub** | Library with known repo | `site:github.com {lib} "{terms}"`, then WebFetch top 2-3 (github.com works fine with WebFetch). |
| **General** | Always | `how to {goal} {lib}`. |
| **Specific** | Error message provided | `"{exact_error_message}" {lib}`. |
| **StackOverflow** | Common problem/implementation pattern | `site:stackoverflow.com {lib} {keywords}`, then `mcp__jina__read_url` top answers (SO is JS-heavy). |
| **Changelog** | Version mentioned OR "stopped working" / "after upgrade" | `{lib} {version} changelog breaking changes migration`. |
| **Best Practices** | Feature implementation (no error) | `{lib} best practices {goal}` + `{lib} recommended architecture {goal}`. |
| **Reddit** | Comparison, best practices, "real world experience" | `site:reddit.com {lib} {keywords}`, then `mcp__jina__read_url` top 2-3 (Reddit is JS-heavy). |
| **Comparison** | "vs", "or", "compare", "which", "best library" | `{A} vs {B} {context}`. |

**Fetching**: prefer `mcp__jina__read_url` for JS-heavy pages (modern docs, SPAs); `WebFetch` for plain HTML and github.com. See "Web Fetching" in CLAUDE.md.

For full agent prompts, see `references/agent-prompts.md`.

### Step 5: Deduplicate and Note Convergence

Wait for agents, deduplicate by URL/issue (keep richest metadata). Note when independent agents found the same source — convergence raises confidence.

### Step 6: Critical Evaluation

**Recency** (adjust by library velocity):

| Age | Fast-moving (React, Next.js) | Stable (Express, lodash) |
|-----|------------------------------|--------------------------|
| < 6 months | High | High |
| 6-18 months | Medium | High |
| 18-36 months | Low | Medium |
| > 3 years | Very Low | Low |

**Authority:**

| Source Type | Score |
|-------------|-------|
| Official docs, changelogs, core team posts, GitHub issues with maintainer response | High |
| GitHub issues (community), recent blogs (named author), SO answers (accepted + >10 votes), comparison articles | Medium |
| Reddit threads (>50 upvotes or multiple experienced replies) | Medium |
| SO answers (not accepted, <10 votes), old blogs, old comparisons | Low |
| Reddit threads (<10 upvotes), random forums | Very Low |

**Popularity signals (don't trust raw star counts):** if a recommendation leans on a library being "popular"/"the standard"/"most-starred" — especially in comparisons or "is this repo trustworthy" questions — a GitHub star count is a vanity metric that is trivially bought and is not evidence of quality or adoption. Cross-check with harder-to-fake signals (fork-to-star ratio, external contributors, production dependents) before weighting it. Quick tell: **>10k stars with a fork-to-star ratio under ~5% is suspicious.** Full checklist and tools in `references/fake-stars.md`.

**Conflicts:** Prefer more recent, then higher authority. If official docs conflict with recent issues, the issue may reveal a bug or undocumented behavior.

### Step 7: Follow-Up Loop (Standard only)

If a topic area has fewer than 2 sources or the core question is unanswered: identify the gap, generate 1-2 delta queries (more specific terms, alternative terminology, broader scope), spawn 1-2 follow-up agents, merge.

**Max 1 cycle.** If the gap persists, mark as low confidence.

### Step 8: Adversarial Critique (Standard only)

Brief self-challenge:
- What would a disagreer cite?
- Over-weighting one source type? (all blogs, no official docs)
- "Independent" sources tracing to one origin? (3 blogs citing one tweet = 1 source)
- Is the recommended approach the simplest, or are we over-engineering?

If the critique reveals a blind spot, adjust and lower confidence.

### Step 9: Present Results

**Lead with the synthesis**, not the raw data. Structure:

1. **Synthesis** — goal, recommended approach, key findings weighted by credibility, **1-3 most influential references** with URLs.
2. **Supporting Details** — only sections relevant and not already covered in the synthesis.

Available detail sections (include only relevant): Documentation · GitHub Issues & Discussions · Reddit · Comparison · Specific Error Matches · Version/Changelog · Conflicts.

For the full output template, see `references/output-format.md`.

## Examples

| # | Query | Spawns |
|---|-------|--------|
| 1 | `research-code how to implement authentication in Next.js 14` | Docs, GitHub, General, Best Practices, StackOverflow |
| 2 | `research-code Redux vs Zustand for large React app` | Docs (both), General, Comparison, Reddit, StackOverflow |
| 3 | `research-code "Cannot read property 'navigate' of undefined" react-navigation` | Docs, GitHub, General, Specific, StackOverflow |
| 4 | `research-code auth navigation not working in react-navigation v7` | Docs, GitHub, General, Changelog, StackOverflow |
| 5 | `research-code best practices for folder structure in Express API` | Docs, General, Best Practices, Reddit, StackOverflow |
| 6 | `research-code what's the default port for Vite dev server` | Quick mode: Docs + General only |

## Troubleshooting

**Agent fails or times out** — Continue with remaining agents. Note the gap in the synthesis.

**No results found** — Widen search terms: try without the library name, use alternative terminology, or search for the underlying concept.

**All sources are outdated** — Flag explicitly. Note dates and recommend verifying against current docs.

**Sources conflict** — Weight by recency and authority. Note the conflict and resolution explaining which to trust and why.
