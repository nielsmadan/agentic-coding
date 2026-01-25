---
name: research-online
description: Research a programming topic online using parallel agents. Searches documentation (via Context7), GitHub issues, general solutions, and specific errors. Use when debugging issues, learning new libraries, or investigating error messages.
argument-hint: <topic or error message>
---

# Research Online

Research a programming topic from multiple angles using parallel sub-agents, with critical evaluation of source credibility.

## Usage

```
/research-online <library> <problem description>
/research-online "<error message>" <library>
/research-online how to implement auth in react-navigation v7
```

## Workflow

### Step 1: Parse Input

Extract from the user's query:
- **Library/framework name** (e.g., "react-navigation", "prisma", "next.js")
- **Error message** (if any, usually in quotes)
- **Version** (if mentioned, e.g., "v7", "version 14")
- **Problem description** (what they're trying to do or what's broken)

### Step 2: Determine Which Agents to Spawn

| Agent | Spawn When | Purpose |
|-------|------------|---------|
| **Docs** | Library/framework mentioned | Context7 documentation lookup |
| **GitHub** | Library with known repository | Search issues for similar problems |
| **General** | Always | Broad "how to" web search |
| **Specific** | Error message provided | Search for exact error text |
| **StackOverflow** | Common problem pattern | Community Q&A solutions |
| **Changelog** | Version mentioned OR "stopped working" / "after upgrade" | Breaking changes, migration guides |

### Step 3: Spawn Agents in Parallel

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

1. First call resolve-library-id with libraryName="{library_name}" and query="{problem_description}"
2. Then call query-docs with the resolved library ID and query="{problem_description}"

Focus on finding:
- API usage relevant to: {problem_description}
- Configuration options
- Common patterns and examples

For each finding, note:
- Source URL
- Date (if available, or note "official docs - current")
- Source type: official docs

Return a concise summary of relevant documentation findings with source metadata.
---
```

#### GitHub Issues Agent
```
Spawn when: Library with known GitHub repo
Subagent type: general-purpose
Prompt template:
---
Search for GitHub issues related to this problem.

Use WebSearch to search: site:github.com {library_name} issues "{key_problem_terms}"

If you find relevant issues:
1. Use WebFetch to read the top 2-3 most relevant issues
2. Extract: problem description, any solutions posted, workarounds mentioned

For each issue, note:
- Issue URL
- Date opened/last updated
- Status (open/closed)
- Whether maintainer responded
- Source type: GitHub issue (maintainer) or GitHub issue (community)

Return a summary of relevant issues and any solutions found with metadata.
---
```

#### General Solutions Agent
```
Spawn when: Always
Subagent type: general-purpose
Prompt template:
---
Search for general solutions to this problem.

Use WebSearch to search: how to {problem_description} {library_name}

Focus on:
- Tutorial articles
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
Spawn when: Common programming problem pattern
Subagent type: general-purpose
Prompt template:
---
Search Stack Overflow for solutions.

Use WebSearch to search: site:stackoverflow.com {library_name} {problem_keywords}

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

Return relevant version changes that might affect: {problem_description}
---
```

### Step 4: Collect Results

Wait for all agents to complete and gather their findings with metadata.

### Step 5: Critical Evaluation

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
| GitHub issues (community) | Medium | Verify with other sources |
| Recent blog (known author) | Medium | Good for tutorials |
| Stack Overflow (accepted, high votes) | Medium | Community validated |
| Stack Overflow (low votes) | Low | Unverified |
| Old blog posts | Low | Often outdated |
| Random forums | Very Low | Last resort |

#### Relevance Score
| Match Type | Score |
|------------|-------|
| Exact error/problem match | High |
| Same library, similar problem | Medium |
| Related library/concept | Low |

#### Conflict Resolution
When sources conflict:
1. Prefer more recent sources
2. Prefer higher authority sources
3. Note the conflict in synthesis
4. If official docs conflict with recent issues, the issue may reveal a bug or undocumented behavior

### Step 6: Present Results

Format the output with source evaluation.

## Output Format

```markdown
## Research Results: {topic}

### Documentation (Context7)
{findings from docs agent}
- Source: {url}
- Authority: High (official docs)

### GitHub Issues
| Issue | Date | Status | Authority | Relevance |
|-------|------|--------|-----------|-----------|
| [#123: {title}]({url}) | 2024-01-15 | Closed | High (maintainer) | High |
| [#456: {title}]({url}) | 2022-03-01 | Open | Medium | Medium |

{summary of solutions found}

### General Solutions
| Source | Date | Authority | Relevance |
|--------|------|-----------|-----------|
| [{title}]({url}) | {date} | {score} | {score} |

{summary of approaches}

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

**Problem:** {one-line summary of what user is trying to solve}

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

### Example 1: Library + Problem
```
/research-online auth navigation not working in react-navigation v7
```
Spawns: Docs, GitHub, General, Changelog (version mentioned)

### Example 2: Specific Error
```
/research-online "Cannot read property 'navigate' of undefined" react-navigation
```
Spawns: Docs, GitHub, General, Specific, StackOverflow

### Example 3: How-to Query
```
/research-online how to implement dark mode in tailwind
```
Spawns: Docs, General, StackOverflow

## Notes

- All agents run in parallel for speed
- Each agent should complete in under 60 seconds
- If an agent fails or finds nothing, note it but continue with others
- Always capture source metadata for critical evaluation
- Weight findings by credibility in synthesis - a recent GitHub issue from a maintainer outweighs a 5-year-old blog post
- Explicitly note when relying on older sources and flag potential staleness
