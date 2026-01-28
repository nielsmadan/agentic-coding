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

Before external research, check if the project has relevant internal docs:

```bash
grep -ri "<relevant_keywords>" docs/ *.md 2>/dev/null | head -10
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

Use the Task tool to spawn ALL relevant agents in a single message (parallel execution).

**Important:** Each agent must capture metadata for critical evaluation:
- Source URL
- Date (when published/posted/updated)
- Source type (official docs / GitHub issue / blog / SO answer / forum)

#### Docs Agent (Context7)
```
Spawn when: Library/framework is identified
Subagent type: general-purpose
Prompt template:
---
Use Context7 to look up documentation for {library_name}.

1. First call resolve-library-id with libraryName="{library_name}" and query="{goal_or_problem}"
2. Then call query-docs with the resolved library ID and query="{goal_or_problem}"

Focus on finding:
- API usage relevant to: {goal_or_problem}
- Configuration options
- Common patterns and examples

For each finding, note:
- Source URL
- Date (if available, or note "official docs - current")
- Source type: official docs

Return a concise summary of relevant documentation findings with source metadata.
---
```

#### GitHub Agent
```
Spawn when: Library with known GitHub repo
Subagent type: general-purpose
Prompt template:
---
Search GitHub for issues AND discussions related to this topic.

Use WebSearch to search: site:github.com {library_name} "{key_terms}"

Look for:
- Issues (bugs, feature requests)
- Discussions (implementation questions, best practices)
- Pull requests with relevant changes

If you find relevant results:
1. Use WebFetch to read the top 2-3 most relevant
2. Extract: problem/question, any solutions posted, recommended approaches

For each result, note:
- URL
- Date opened/last updated
- Type (issue/discussion/PR)
- Status (open/closed/merged)
- Whether maintainer responded
- Source type: GitHub issue (maintainer) / GitHub issue (community) / GitHub discussion

Return a summary of relevant findings with metadata.
---
```

#### General Solutions Agent
```
Spawn when: Always
Subagent type: general-purpose
Prompt template:
---
Search for general solutions and guides for this topic.

Use WebSearch to search: how to {goal_or_problem} {library_name}

Focus on:
- Tutorial articles
- Implementation guides
- Blog posts with solutions
- Official guides

For each source, note:
- Source URL
- Publication date (look for date in article or URL)
- Source type: blog / tutorial / official guide
- Author credibility if apparent (known developer, company blog, random post)

Return a summary of approaches found with source metadata.
---
```

#### Specific Error Agent
```
Spawn when: Error message is provided
Subagent type: general-purpose
Prompt template:
---
Search for this specific error message.

Use WebSearch to search: "{exact_error_message}" {library_name}

Find:
- What causes this error
- How others have fixed it
- Any library-specific solutions

For each source, note:
- Source URL
- Date
- Source type
- Whether it's an exact match for the error or similar

Return findings with the most common causes and fixes, including source metadata.
---
```

#### Stack Overflow Agent
```
Spawn when: Common programming problem or implementation pattern
Subagent type: general-purpose
Prompt template:
---
Search Stack Overflow for solutions and implementations.

Use WebSearch to search: site:stackoverflow.com {library_name} {keywords}

For the top 2-3 relevant questions:
1. Use WebFetch to read the accepted/top answers
2. Extract the solution approach

For each answer, note:
- Question URL
- Answer date
- Vote count
- Whether it's the accepted answer
- Source type: SO answer (accepted/high-votes) or SO answer (low-votes)

Return a summary of community solutions with metadata.
---
```

#### Changelog Agent
```
Spawn when: Version mentioned OR upgrade-related problem
Subagent type: general-purpose
Prompt template:
---
Search for changelog and breaking changes.

Use WebSearch to search: {library_name} {version} changelog breaking changes migration

Find:
- What changed in this version
- Known breaking changes
- Migration guides

For each source, note:
- Source URL
- Date/version it covers
- Source type: official changelog / migration guide / release notes

Return relevant version changes that might affect: {goal_or_problem}
---
```

#### Best Practices Agent
```
Spawn when: Feature implementation query (no error message present)
Subagent type: general-purpose
Prompt template:
---
Search for best practices and recommended patterns.

Use WebSearch to search: {library_name} best practices {goal_description}
Also search: {library_name} recommended architecture {goal_description}

Focus on:
- Official style guides and recommendations
- Architecture patterns from experienced developers
- Common pitfalls to avoid
- Production-ready patterns

For each source, note:
- Source URL
- Publication date
- Source type: official guide / architecture blog / tutorial
- Author credibility (core team, recognized expert, unknown)

Return a summary of recommended approaches with source metadata.
---
```

#### Comparison Agent
```
Spawn when: Query contains "vs", "or", "compare", "which", "best library/package"
Subagent type: general-purpose
Prompt template:
---
Search for comparisons between the options mentioned.

Use WebSearch to search: {option_A} vs {option_B} {context}
Also search: {option_A} or {option_B} which is better {context}

Find:
- Direct comparison articles
- Pros and cons of each option
- Performance benchmarks if relevant
- Use case recommendations (when to use which)

For each source, note:
- Source URL
- Publication date (crucial for comparisons - libraries change fast)
- Source type: comparison article / benchmark / discussion
- Whether it covers recent versions

Return a balanced summary of each option's strengths and weaknesses with source metadata.
---
```

### Step 5: Collect Results

Wait for all agents to complete and gather their findings with metadata.

### Step 6: Critical Evaluation

Before synthesizing, evaluate each source using these criteria:

#### Recency Score
| Age | Score | Notes |
|-----|-------|-------|
| < 6 months | High | Likely current |
| 6-18 months | Medium | Check for updates |
| 18+ months | Low | May be outdated |
| > 3 years | Very Low | Likely outdated, verify still applies |

**Adjust for library velocity:** Fast-moving libraries (React, Next.js, Prisma) decay faster than stable ones (lodash, express).

#### Authority Score
| Source Type | Score | Notes |
|-------------|-------|-------|
| Official docs | High | Authoritative but may lag features |
| GitHub issues (maintainer response) | High | Direct from source |
| Official changelog/release notes | High | Definitive for version info |
| Core team blog posts | High | Authoritative for patterns |
| GitHub issues (community) | Medium | Verify with other sources |
| Recent blog (known author) | Medium | Good for tutorials |
| Stack Overflow (accepted, high votes) | Medium | Community validated |
| Comparison articles (recent) | Medium | Useful but check bias |
| Stack Overflow (low votes) | Low | Unverified |
| Old blog posts | Low | Often outdated |
| Old comparisons | Low | Libraries change significantly |
| Random forums | Very Low | Last resort |

#### Relevance Score
| Match Type | Score |
|------------|-------|
| Exact error/goal match | High |
| Same library, similar task | Medium |
| Related library/concept | Low |

#### Conflict Resolution
When sources conflict:
1. Prefer more recent sources
2. Prefer higher authority sources
3. Note the conflict in synthesis
4. If official docs conflict with recent issues, the issue may reveal a bug or undocumented behavior

### Step 7: Present Results

Format the output with source evaluation.

## Output Format

```markdown
## Research Results: {topic}

### Documentation (Context7)
{findings from docs agent}
- Source: {url}
- Authority: High (official docs)

### GitHub Issues & Discussions
| Item | Date | Type | Authority | Relevance |
|------|------|------|-----------|-----------|
| [#123: {title}]({url}) | 2024-01-15 | Issue | High (maintainer) | High |
| [{title}]({url}) | 2024-02-01 | Discussion | Medium | High |

{summary of solutions/approaches found}

### General Solutions
| Source | Date | Authority | Relevance |
|--------|------|-----------|-----------|
| [{title}]({url}) | {date} | {score} | {score} |

{summary of approaches}

### Best Practices
(only if feature implementation query)
| Source | Date | Authority |
|--------|------|-----------|
| [{title}]({url}) | {date} | {score} |

{recommended patterns and approaches}

### Comparison
(only if comparison query)
| Source | Date | Authority | Covers Current Versions |
|--------|------|-----------|------------------------|
| [{title}]({url}) | {date} | {score} | Yes/No |

**{Option A}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}

**{Option B}:**
- Pros: {list}
- Cons: {list}
- Best for: {use cases}

### Specific Error Matches
(only if error was provided)
| Source | Date | Authority | Match |
|--------|------|-----------|-------|
| [{title}]({url}) | {date} | {score} | Exact/Similar |

{causes and fixes}

### Stack Overflow
| Question | Date | Votes | Accepted |
|----------|------|-------|----------|
| [{title}]({url}) | {date} | {count} | Yes/No |

{community solutions}

### Version/Changelog
(only if version was mentioned)
{breaking changes and migration info}

---

## Source Evaluation Summary

**Most Credible Sources:**
1. {source} - {reason: e.g., "Official docs + exact match"}
2. {source} - {reason: e.g., "Recent GitHub issue with maintainer fix"}

**Potentially Outdated (use with caution):**
- {source} from {date} - verify still applies to current version

**Conflicts Found:**
- {source A} says X, but {source B} says Y
- **Resolution:** {which to trust and why}

---

## Synthesis

**Goal:** {one-line summary of what user is trying to achieve}

**Key Findings (weighted by credibility):**
- {finding from high-credibility source}
- {finding from high-credibility source}
- {finding from medium source, noting caveat if needed}

**Recommended Approach:**
{what the research suggests, prioritizing recent authoritative sources}

**Confidence:** {High/Medium/Low}
- Based on: {e.g., "3 high-credibility sources agree"}
- Caveats: {any outdated info factored in, unresolved conflicts, gaps in research}
```

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

## Notes

- All agents run in parallel for speed
- Each agent should complete in under 60 seconds
- If an agent fails or finds nothing, note it but continue with others
- Always capture source metadata for critical evaluation
- Weight findings by credibility in synthesis - a recent GitHub issue from a maintainer outweighs a 5-year-old blog post
- Explicitly note when relying on older sources and flag potential staleness
- For comparisons, be especially careful about recency - library landscapes change quickly
