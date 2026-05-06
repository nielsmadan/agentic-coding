# Output Format Template

Lead with the synthesis, then include only supporting detail sections relevant to the query. Skip sections that would repeat the synthesis.

```markdown
## Research Results: {topic}

### Synthesis

**Question:** {one-line restatement of what the user wants to know}

**Best Answer:**
{what the evidence shows, weighted by source authority and topic stability — primary sources and peer-reviewed work first for empirical questions; primary documents for historical}

**Key Findings (weighted by credibility):**
- {finding from high-credibility source — e.g., meta-analysis or primary document}
- {finding from high-credibility source}
- {finding from medium source, noting caveat — e.g., "single study", "advocacy source", "preliminary data"}

**Confidence:** {High / Medium / Low}
- Based on: {e.g., "convergent findings across 1 meta-analysis and 2 primary studies"}
- Caveats: {scope mismatches, contested areas, gaps in evidence, recency concerns for fast-moving topics}

**Key References:**
1. [{title}]({url}) — {why this source matters, e.g., "2023 meta-analysis pooling 47 studies"}
2. [{title}]({url}) — {why this source matters, e.g., "primary government data"}
3. [{title}]({url}) — {why this source matters} (optional, only if 3rd source significantly shaped the conclusion)

---

### Supporting Details

(Include only sections relevant to the query, and only findings not already covered in the synthesis above)

#### Background
(only when grounding is useful — e.g., topic involves contested terminology or unfamiliar entities)
{Wikipedia / encyclopedic context with the entry's own cited sources}

#### Evidence
(empirical / scientific / scholarly questions)
- **{Finding}** — {study type, sample, date, citation}. {What it shows.}
- **{Finding}** — {study type, sample, date, citation}. {What it shows.}

Include where studies disagree and what drives the disagreement (sample, endpoint, methodology).

#### News & Reporting
(current events or contemporaneous coverage)
- **{Outlet, date}** — {what was reported, with primary-vs-secondary distinction}

#### Comparison
(only if comparison query)

**{Option A}:**
- Strengths: {list}
- Weaknesses: {list}
- Best for: {use cases / contexts}

**{Option B}:**
- Strengths: {list}
- Weaknesses: {list}
- Best for: {use cases / contexts}

Note where the choice depends on values vs. where there's an empirical answer.

#### Claim Verification
(only if user provided a specific claim to verify)
- **The claim:** "{exact_claim}"
- **Verdict:** {true / mostly true / mixed / mostly false / false / unproven}
- **Strongest evidence for:** {source(s)}
- **Strongest evidence against:** {source(s)}
- **Origin of the claim:** {original source if findable, or "untraceable"}

#### Historical Context
(only if historical query)
- **Primary documents:** {list with dates}
- **Contemporaneous reporting:** {list with dates and outlets}
- **Historiographical debate:** {where established historians disagree, if relevant}

#### Conflicts
(only if sources disagree on something material)
- {source A} says X, but {source B} says Y
- **Resolution:** {which to trust and why — authority, scope, recency, primary vs secondary}
- {or note the conflict is unresolved by the evidence available}

#### Open Questions
(what the search did not resolve)
- {gap}: {why it persisted — e.g., "no peer-reviewed data on this population", "primary documents still classified"}
```
