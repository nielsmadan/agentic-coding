# Output Format Template

Full output format for research results. Include only the sections relevant to the query type.

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
