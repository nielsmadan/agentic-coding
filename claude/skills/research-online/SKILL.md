---
name: research-online
description: Research a programming topic online from multiple sources. Use when implementing features, learning new libraries, or debugging issues.
argument-hint: <topic or error message>
---

# Research Online

Research a programming topic from multiple angles using parallel sub-agents, with critical evaluation of source credibility.

## Usage

```
/research-online <library> <what you want to do>
/research-online "<error message>" <library>
/research-online how to implement auth in react-navigation v7
/research-online best practices for state management in React
/research-online Redux vs Zustand for large app
```

## Workflow

### Step 1: Parse Input

Extract from the user's query:
- **Library/framework name** (e.g., "react-navigation", "prisma", "next.js")
- **Error message** (if any, usually in quotes)
- **Version** (if mentioned, e.g., "v7", "version 14")
- **Goal/intent** (what they're trying to build or achieve)
- **Problem description** (if debugging: what's broken or unexpected)
- **Comparison targets** (if comparing: "X vs Y", "X or Y")

### Step 2: Check Internal Documentation First

Before external research, use the Grep tool to search for relevant keywords in the project's docs:

```
Grep pattern: "<relevant_keywords>" path: "docs/" and "*.md"
```

If found, read and include internal patterns/conventions in the synthesis. Internal docs often contain project-specific decisions that external research won't cover.

### Step 3: Determine Which Agents to Spawn

| Agent | Spawn When | Purpose |
|-------|------------|---------|
| **Docs** | Library/framework mentioned | Context7 documentation lookup |
| **GitHub** | Library with known repository | Search issues AND discussions |
| **General** | Always | Broad "how to" web search |
| **Specific** | Error message provided | Search for exact error text |
| **StackOverflow** | Common problem/implementation pattern | Community Q&A solutions |
| **Changelog** | Version mentioned OR "stopped working" / "after upgrade" | Breaking changes, migration guides |
| **Best Practices** | Feature implementation (no error message) | Architecture patterns, recommended approaches |
| **Comparison** | Query contains "vs", "or", "compare", "which", "best library" | Compare options, pros/cons |

### Step 4: Spawn Agents in Parallel

Use the Task tool to spawn ALL relevant agents in a **single message** (parallel execution). Each agent uses `subagent_type: general-purpose`.

**Every agent must capture metadata for each source:** URL, date, and source type (official docs / GitHub issue / blog / SO answer / forum).

| Agent | Tool | Search Strategy |
|-------|------|-----------------|
| Docs | Context7 | resolve-library-id then query-docs |
| GitHub | WebSearch | `site:github.com {lib} "{terms}"`, then WebFetch top 2-3 |
| General | WebSearch | `how to {goal} {lib}` |
| Specific | WebSearch | `"{exact_error_message}" {lib}` |
| StackOverflow | WebSearch | `site:stackoverflow.com {lib} {keywords}`, then WebFetch top answers |
| Changelog | WebSearch | `{lib} {version} changelog breaking changes migration` |
| Best Practices | WebSearch | `{lib} best practices {goal}` + `{lib} recommended architecture {goal}` |
| Comparison | WebSearch | `{option_A} vs {option_B} {context}` |

For full agent prompt templates with detailed instructions, see `references/agent-prompts.md`.

### Step 5: Collect Results

Wait for all agents to complete and gather their findings with metadata.

### Step 6: Critical Evaluation

Before synthesizing, evaluate each source:

**Recency:**

| Age | Score | Notes |
|-----|-------|-------|
| < 6 months | High | Likely current |
| 6-18 months | Medium | Check for updates |
| 18+ months | Low | May be outdated |
| > 3 years | Very Low | Likely outdated, verify |

Adjust for library velocity: fast-moving libraries (React, Next.js) decay faster than stable ones (Express, lodash).

**Authority:**

| Source Type | Score |
|-------------|-------|
| Official docs, changelogs, core team posts | High |
| GitHub issues (maintainer response) | High |
| GitHub issues (community), recent blogs (known author) | Medium |
| SO answers (accepted, high votes), comparison articles | Medium |
| SO answers (low votes), old blogs, old comparisons | Low |
| Random forums | Very Low |

**Relevance:** Exact error/goal match = High. Same library, similar task = Medium. Related concept = Low.

**When sources conflict:** Prefer more recent, then higher authority. Note conflicts in synthesis. If official docs conflict with recent issues, the issue may reveal a bug or undocumented behavior.

### Step 7: Present Results

Structure the output with these sections (include only those relevant to the query):

1. **Documentation** — Context7 findings with authority rating
2. **GitHub Issues & Discussions** — table with date, type, authority, relevance
3. **General Solutions** — table with source, date, authority
4. **Best Practices** — (feature queries only) recommended patterns
5. **Comparison** — (comparison queries only) pros/cons/best-for per option
6. **Specific Error Matches** — (error queries only) causes and fixes
7. **Stack Overflow** — question table with date, votes, accepted status
8. **Version/Changelog** — (version queries only) breaking changes
9. **Source Evaluation Summary** — most credible, potentially outdated, conflicts found
10. **Synthesis** — goal, key findings weighted by credibility, recommended approach, confidence level

For the full output format template with markdown tables, see `references/output-format.md`.

## Examples

### Example 1: Feature Implementation
```
/research-online how to implement authentication in Next.js 14
```
Spawns: Docs, GitHub, General, Best Practices, StackOverflow

### Example 2: Comparison Query
```
/research-online Redux vs Zustand for large React app
```
Spawns: Docs (both), General, Comparison, StackOverflow

### Example 3: Specific Error
```
/research-online "Cannot read property 'navigate' of undefined" react-navigation
```
Spawns: Docs, GitHub, General, Specific, StackOverflow

### Example 4: Version-Specific
```
/research-online auth navigation not working in react-navigation v7
```
Spawns: Docs, GitHub, General, Changelog, StackOverflow

### Example 5: Best Practices
```
/research-online best practices for folder structure in Express API
```
Spawns: Docs, General, Best Practices, StackOverflow

## Troubleshooting

### Agent fails or times out
**Solution:** Continue with remaining agents. Note the gap in the synthesis and which source types are missing. The research is still useful with partial results.

### No results found for a query
**Solution:** Widen search terms — try without the library name, use alternative terminology, or search for the underlying concept rather than the specific implementation.

### All sources are outdated
**Solution:** Flag explicitly in the synthesis. Note the dates and recommend the user verify against current documentation. Prefer official docs over old blog posts.

### Sources conflict with each other
**Solution:** Weight by recency and authority. Note the conflict clearly in the Source Evaluation Summary with a resolution explaining which source to trust and why.

## Notes

- All agents run in parallel for speed
- Each agent should complete in under 60 seconds
- Always capture source metadata for critical evaluation
- Weight findings by credibility in synthesis — a recent GitHub issue from a maintainer outweighs a 5-year-old blog post
- For comparisons, be especially careful about recency — library landscapes change quickly
