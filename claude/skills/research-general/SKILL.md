---
name: research-general
description: Research a non-programming topic online from multiple sources — scientific, historical, current events, policy, comparisons, fact-checking. Use when asking "what does the research say about X", "what caused Y", "X vs Y" (non-tech), or verifying a claim. For programming topics use the `research-online` skill instead.
argument-hint: <topic, question, or claim to verify>
---

# Research General

Research a general (non-programming) topic from multiple angles using parallel sub-agents, with critical evaluation of source credibility.

## Usage

```
research-general <question or topic>
research-general "<exact claim to verify>"
research-general what does the evidence say about screen time and adolescent sleep
research-general causes of the 2008 financial crisis
research-general nuclear vs solar economics for grid power
research-general history of the Suez Canal crisis
```

## Gotchas
- "Recent" doesn't mean "correct". For historical, philosophical, or settled empirical topics, a 30-year-old peer-reviewed paper can outweigh a recent op-ed. Weigh authority and topic-stability before recency.
- Wikipedia is great for **grounding** (terminology, entity names, citation trail) but not as a final authority — follow its citations to primary sources before stating something as fact.
- Advocacy organizations and think tanks have a stance. Cite them as evidence of *what that side says*, not as neutral fact. Look for opposing primary sources before concluding.
- Quick mode may miss nuance. If a seemingly factual question turns out to be contested (e.g., "Is X healthy?" — depends on dose, population, endpoint), note this in the synthesis and suggest re-running in Standard mode.

## Workflow

### Step 1: Parse Input

Extract from the user's query:
- **Topic / question** (e.g., "screen time and sleep", "Suez Canal crisis", "intermittent fasting")
- **Sub-questions or claims** (if the user is asking a multi-part question, or a specific claim to verify)
- **Date scope** (if mentioned: "in the last decade", "since 2020", historical period)
- **Comparison targets** (if comparing: "X vs Y", "X or Y", "differences between X and Y")
- **Geographic / population scope** (if relevant: "in the EU", "in adolescents", "in low-income countries")
- **Topic stability** (rough call: current events / active research / established / historical) — drives the recency rubric and which agents to spawn

### Step 2: Classify Query Depth

Classify the query to avoid over-researching simple questions:

| Mode | When | Behavior |
|------|------|----------|
| **Quick** | Well-known fact, one-shot lookup ("capital of X", "when did Y happen", "who founded Z") | Spawn only Encyclopedic + General (max 2 agents). Skip follow-up loop and critique. Go straight to synthesis. |
| **Standard** | Empirical questions, contested topics, comparisons, fact-checking, "what caused", "what does the research say" | Full workflow including follow-up loop and adversarial critique |

When in doubt, use Standard. Anything that hinges on evidence or interpretation is Standard.

### Step 3: Determine Which Agents to Spawn

| Agent | Spawn When | Purpose |
|-------|------------|---------|
| **Encyclopedic** | Almost always | Wikipedia for grounding — terminology, entity overview, citation trail to primary sources |
| **Academic** | Scientific, empirical, scholarly, social-science, or economic question | Peer-reviewed papers and preprints (arxiv/SSRN) for evidence |
| **News** | Current events, recent developments, contemporaneous reporting on historical events | Established news outlets |
| **Primary** | Statistics, official positions, regulatory questions, government action | Government data, official organization reports, regulator filings |
| **General** | Always | Broad web search for guides, explainers, surveys |
| **Forum** | Opinion-heavy questions ("is X worth it?", lived experience), unsettled topics | Reddit / community forums for candid views |
| **Comparison** | Query contains "vs", "or", "compare", "which is better", "differences between" | Direct comparison sources, pros/cons |
| **Specific** | Exact claim or quote to verify (typically in quotes) | Verify or refute the literal claim |
| **Historical** | Topic is historical OR a historical angle is needed | Primary documents, archived reporting, established historians |

### Step 4: Spawn Agents in Parallel

Use the Task tool to spawn ALL relevant agents in a **single message** (parallel execution). Each agent uses `subagent_type: general-purpose`.

**Every agent must capture metadata for each source:** URL, date, source type, author/publisher, and (where it applies) sample size / methodology / primary-vs-secondary status.

| Agent | Tool | Search Strategy |
|-------|------|-----------------|
| Encyclopedic | WebSearch | `site:en.wikipedia.org {topic}`, then `mcp__jina__read_url` on top 1-2 articles. Note Wikipedia's own cited sources for follow-up. |
| Academic | `mcp__jina__parallel_search_arxiv` for STEM, `mcp__jina__parallel_search_ssrn` for econ/finance/law/social science. Fall back to WebSearch `site:scholar.google.com` or `{topic} systematic review meta-analysis`. |
| News | WebSearch | `{topic}` filtered to known outlets (NYT, BBC, Reuters, AP, Guardian, Economist, FT, NPR, WSJ). Then `mcp__jina__read_url` on top 2-3. |
| Primary | WebSearch | `{topic} site:.gov` or `site:.int` or `{org} report {topic}`. Fetch with WebFetch (gov pages usually plain HTML) or Jina if JS-heavy. |
| General | WebSearch | `{topic}` plain — surfaces explainers, longreads, expert blogs |
| Forum | WebSearch | `site:reddit.com {topic}`, then `mcp__jina__read_url` top 2-3 threads (Reddit is JS-heavy) |
| Comparison | WebSearch | `{option_A} vs {option_B} {context}`, plus `{option_A} or {option_B} which` |
| Specific | WebSearch | `"{exact_claim}"` plus `"{exact_claim}" fact check` and `"{exact_claim}" debunked` |
| Historical | WebSearch | `{topic} primary sources`, `{topic} archive`, `{topic} declassified`. Try news archives (e.g., `site:nytimes.com/{year}/`). |

**Fetching note**: prefer `mcp__jina__read_url` for JS-heavy pages (Reddit, modern news SPAs); use `WebFetch` for plain HTML, government PDFs, and `.gov`/`.int` sites. If one returns thin content, retry with the other. See "Web Fetching" in CLAUDE.md.

For full agent prompt templates, see `references/agent-prompts.md`.

### Step 5: Collect and Deduplicate Results

Wait for all agents to complete and gather findings with metadata. Deduplicate: if multiple agents found the same URL or paper, keep the entry with the richest metadata and merge unique context. Note convergence — if Encyclopedic, Academic, and News all surface the same primary source, that source's authority gets reinforced.

**Watch for false convergence**: three blogs all citing the same single tweet are *one* source, not three. Trace claims to their original.

### Step 6: Critical Evaluation

Before synthesizing, evaluate each source on three axes:

**Authority:**

| Source Type | Score |
|-------------|-------|
| Peer-reviewed papers (esp. systematic reviews / meta-analyses), government statistics, primary-source documents, encyclopedia entries with strong citations | High |
| Established news outlets with reporting standards (NYT, BBC, Reuters, AP, Economist, FT), reputable books, official organization reports | High |
| Working papers / preprints (arxiv/SSRN), expert blogs by named verified experts, Wikipedia articles (no dispute markers, well-cited), think-tank reports | Medium |
| Secondary news outlets, op-eds by named experts, podcast claims by named experts | Medium |
| Reddit threads (>100 upvotes with substantive replies), well-engaged forum discussions | Medium-Low |
| Op-eds without named expertise, advocacy organization claims about their own cause, single-source articles | Low |
| Anonymous forums (low engagement), unsourced articles, content farms, social media posts | Very Low |

**Recency** (depends on topic stability — match the query's domain):

| Topic Type | Age Threshold for "Recent Enough" |
|-----------|-----------------------------------|
| Current events, market data, active policy | < 1 month, often < 1 week |
| Active research, contested empirical questions, public health | < 5 years preferred; older OK if cited as foundational |
| Established science, well-settled history, mathematics, philosophy | Recency mostly irrelevant; check for recent refinements |
| Historical / biographical / classical | Recency irrelevant; **primary sources preferred over recent commentary** |

**Relevance:** Direct match to query = High. Same domain, adjacent question = Medium. Tangentially related = Low.

**When sources conflict:** First check if it's a real conflict or different scopes / populations / endpoints. Real conflicts: prefer higher authority, then more recent, then primary over secondary. Note material conflicts in the synthesis. If a peer-reviewed meta-analysis disagrees with mainstream news coverage, the meta-analysis usually wins on the empirical question — but the news may correctly capture *what people believe*.

### Step 7: Follow-Up Search Loop (Standard mode only)

After critical evaluation, check if any topic area has **fewer than 2 sources** or if the query's core question remains unanswered. If so:

1. Identify the gap (e.g., "no primary source found for the casualty figures")
2. Generate 1-2 targeted delta queries — alternative terminology, narrower or broader scope, primary-source angle
3. Spawn 1-2 follow-up agents
4. Merge new results, deduplicate, re-evaluate

**Max 1 follow-up cycle.** If the gap persists, note it in the synthesis as a low-confidence area rather than searching again.

### Step 8: Adversarial Critique (Standard mode only)

Brief self-challenge before presenting. Ask:

- What would someone who disagrees with this conclusion cite? Did the search find that?
- Are we over-weighting one source type? (e.g., all findings from news, no academic; or all academic, no real-world data)
- Could "independent" sources actually trace back to a single original? (3 articles citing one study = 1 source on the empirical question)
- Are we mistaking *what people say is true* for *what is actually true*? News coverage of a claim ≠ evidence for the claim.
- Is there a population, scope, or endpoint mismatch between the user's question and the evidence found?

If the critique reveals a blind spot, adjust the synthesis and lower the confidence level.

### Step 9: Present Results

**Lead with the synthesis, not the raw data.** The user wants the answer first, with evidence behind it.

Structure the output as:

1. **Synthesis** — question, current best answer, confidence level, key findings weighted by credibility. Include the **1-3 most influential references** with URLs — the sources that most shaped the conclusion.
2. **Supporting Details** — only sections relevant to the query, and only findings not already covered in the synthesis.

Available detail sections (include only those relevant):
- **Background** — Wikipedia/encyclopedic grounding if needed
- **Evidence** — academic / primary-source findings, with study type and date
- **News & Reporting** — contemporaneous coverage with dates and outlets
- **Comparison** — (comparison queries only) per-option strengths/weaknesses
- **Claim Verification** — (specific-claim queries only) what the claim says vs. what evidence shows
- **Historical Context** — (historical queries only) primary documents and archived reporting
- **Conflicts** — only if sources disagree on something material, with resolution
- **Open Questions** — what the search did not resolve

For the full output format template, see `references/output-format.md`.

## Examples

### Example 1: Empirical Question
```
research-general what does the evidence say about screen time and adolescent sleep
```
Spawns: Encyclopedic, Academic, News, Forum, General

### Example 2: Historical Causation
```
research-general causes of the 2008 financial crisis
```
Spawns: Encyclopedic, Academic, News (archived), Primary (Fed/SEC), Comparison (theories)

### Example 3: Comparison Query
```
research-general nuclear vs solar economics for grid power
```
Spawns: Academic, Primary (gov energy data), Comparison, News, Encyclopedic

### Example 4: Historical Topic
```
research-general history of the Suez Canal crisis
```
Spawns: Encyclopedic, Historical, News (archived), Primary (declassified docs)

### Example 5: Claim Verification
```
research-general "humans only use 10% of their brain"
```
Spawns: Specific, Academic, Encyclopedic, General

### Example 6: Quick Mode (Simple Lookup)
```
research-general what's the capital of Mongolia
```
Quick mode: Spawns Encyclopedic + General only. Returns direct answer without follow-up loop or critique.

## Troubleshooting

### Agent fails or times out
**Solution:** Continue with remaining agents. Note the gap in the synthesis and which source types are missing.

### No academic sources found
**Solution:** Try alternative terms (medical/scientific terminology often differs from lay language). If still nothing, the topic may not have empirical literature — note this and rely on primary/encyclopedic/news sources, marking confidence accordingly.

### Sources disagree along ideological lines
**Solution:** Separate the empirical claim from the value judgment. Find the underlying primary source both sides cite (or fail to cite). Present what each side argues, then what the primary evidence supports — and note where the disagreement is genuinely values-based rather than factual.

### Topic is current and unsettled
**Solution:** Flag explicitly — "this is an active situation as of {date}; details may shift." Prefer wire services (Reuters, AP) over editorial outlets for fast-moving events.

## Notes

- All agents run in parallel for speed
- Each agent should complete in under 60 seconds
- Always capture source metadata for critical evaluation
- Weight findings by credibility — a meta-analysis outweighs a popular blog post on an empirical question
- For historical topics, **primary sources beat recent commentary** — invert the usual recency preference
- Follow Wikipedia's citations down to the primary source rather than citing Wikipedia itself
